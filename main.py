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

os.environ["OPENAI_API_KEY"] = os.getenv('API_KEY')

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
    vectorstore = Chroma.from_documents(chunks, embeddings, persist_directory="./db")
    vectorstore.persist()

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



all_docs = load_documents("CV.pdf", "JD.txt", jd_type="txt")
retriever = prepare_retriever(all_docs)


qa_chain, memory = create_conversational_chain(retriever)

response1 = qa_chain({"question": "Does the candidate have AWS experience?"})
print("Answer 1:", response1["answer"])

response2 = qa_chain({"question": "What about their NLP skills?"})
print("Answer 2:", response2["answer"])


