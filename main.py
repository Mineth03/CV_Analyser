from fastapi import FastAPI, UploadFile, Request
from fastapi.middleware.cors import CORSMiddleware
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import PDFMinerLoader, TextLoader
from langchain.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from dotenv import load_dotenv
import os

load_dotenv()
os.environ["OPENAI_API_KEY"] = os.getenv("API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory = None
qa_chain = None


def load_documents(cv_pdf_path, jd_input, jd_type=""):
    cv_loader = PDFMinerLoader(cv_pdf_path)
    cv_docs = cv_loader.load()

    if jd_type == "pdf":
        jd_loader = PDFMinerLoader(jd_input)
        jd_docs = jd_loader.load()
    elif jd_type == "txt":
        jd_loader = TextLoader(jd_input)
        jd_docs = jd_loader.load()
    elif jd_type == "text":
        jd_docs = [Document(page_content=jd_input, metadata={"source": "user_input"})]
    else:
        raise ValueError("Invalid JD type. Choose from 'pdf', 'txt', or 'text'.")

    return cv_docs + jd_docs


def prepare_retriever(documents):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(chunks, embeddings)
    return vectorstore.as_retriever()


custom_prompt = PromptTemplate(
    template="""
You are an expert HR assistant helping to analyze a candidate's CV against a job description.

Use ONLY the provided context to answer the question.
If the context does not contain relevant information, reply with "I don't have enough information."

Context:
{context}

Question:
{question}

Answer:
""",
    input_variables=["context", "question"]
)


def create_conversational_chain(retriever):
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chat_llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)

    qa_chain = ConversationalRetrievalChain.from_llm(
        llm=chat_llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": custom_prompt}
    )

    return qa_chain, memory


@app.post("/upload")
async def upload_files(cv_file: UploadFile, jd_file: UploadFile):
    global qa_chain, memory

    cv_path = f"./{cv_file.filename}"
    jd_path = f"./{jd_file.filename}"

    with open(cv_path, "wb") as f:
        f.write(await cv_file.read())
    with open(jd_path, "wb") as f:
        f.write(await jd_file.read())

    jd_filetype = "pdf" if jd_file.filename.lower().endswith(".pdf") else "txt"

    all_docs = load_documents(cv_path, jd_path, jd_type=jd_filetype)
    retriever = prepare_retriever(all_docs)
    qa_chain, memory = create_conversational_chain(retriever)

    os.remove(cv_path)
    os.remove(jd_path)

    return {"message": "Files uploaded and model initialized successfully."}



@app.post("/ask")
async def ask_question(request: Request):
    global qa_chain
    if not qa_chain:
        return {"answer": "Please upload CV and JD first."}

    data = await request.json()
    question = data.get("question")

    response = qa_chain.invoke({"question": question})
    return {"answer": response["answer"]}
