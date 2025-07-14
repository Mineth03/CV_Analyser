import { useState, useRef, useEffect } from 'react';
import axios from 'axios';

function App() {
  const [cvFile, setCvFile] = useState(null);
  const [jdFile, setJdFile] = useState(null);
  const [uploaded, setUploaded] = useState(false);

  const [question, setQuestion] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [loading, setLoading] = useState(false);

  const chatBoxRef = useRef(null);

  const handleUpload = async () => {
    if (!cvFile || !jdFile) {
      alert('Please upload both CV and JD.');
      return;
    }

    const formData = new FormData();
    formData.append('cv_file', cvFile);
    formData.append('jd_file', jdFile);

    try {
      setLoading(true);
      await axios.post('http://localhost:8000/upload', formData);
      setUploaded(true);
    } catch (error) {
      console.error('Upload failed:', error);
      alert('Upload failed. Check console for details.');
    } finally {
      setLoading(false);
    }
  };

  const handleSendMessage = async () => {
    if (!question) return;

    const newMessage = { type: 'user', text: question };
    setChatHistory((prev) => [...prev, newMessage]);
    setQuestion('');
    setLoading(true);

    try {
      const res = await axios.post('http://localhost:8000/ask', { question });
      const botMessage = { type: 'bot', text: res.data.answer };
      setChatHistory((prev) => [...prev, botMessage]);
    } catch (error) {
      console.error('Failed to get answer:', error);
      const errorMessage = { type: 'bot', text: 'Error fetching answer.' };
      setChatHistory((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (chatBoxRef.current) {
      chatBoxRef.current.scrollTop = chatBoxRef.current.scrollHeight;
    }
  }, [chatHistory]);

  return (
    <div className="h-screen flex bg-black text-white font-sans">
      {/* Left Panel - Upload Section */}
      <div className="w-1/3 bg-gray-900 p-6 flex flex-col justify-center space-y-4 border-r border-gray-700">
        <h2 className="text-2xl font-bold text-center mb-4 text-[#1DCD9F]">Upload CV & JD</h2>

        <label className="bg-[#1DCD9F] text-black px-4 py-2 rounded cursor-pointer text-center">
          Choose CV
          <input type="file" onChange={(e) => setCvFile(e.target.files[0])} className="hidden" />
        </label>
        {cvFile && <p className="text-sm text-center text-gray-300">{cvFile.name}</p>}

        <label className="bg-[#1DCD9F] text-black px-4 py-2 rounded cursor-pointer text-center">
          Choose JD
          <input type="file" onChange={(e) => setJdFile(e.target.files[0])} className="hidden" />
        </label>
        {jdFile && <p className="text-sm text-center text-gray-300">{jdFile.name}</p>}

        <button
          onClick={handleUpload}
          disabled={loading}
          className="bg-[#169976] hover:bg-[#1DCD9F] text-white px-4 py-2 rounded transition w-full"
        >
          {loading ? 'Uploading...' : 'Upload'}
        </button>
      </div>

      {/* Right Panel - Chat Section */}
      <div className="w-2/3 flex flex-col bg-[#222222]">
        <div className="p-4 border-b border-gray-700 text-center text-2xl font-bold text-[#1DCD9F]">
          CV & JD Analyser Chat
        </div>

        <div
          ref={chatBoxRef}
          className="flex-1 overflow-y-auto p-4 space-y-2 bg-gray-800"
        >
          {chatHistory.map((msg, index) => (
            <div
              key={index}
              className={`p-2 rounded max-w-xs ${
                msg.type === 'user'
                  ? 'bg-[#1DCD9F] text-black self-end ml-auto'
                  : 'bg-[#169976] text-white self-start mr-auto'
              }`}
            >
              {msg.text}
            </div>
          ))}
        </div>

        {uploaded && (
          <div className="p-4 border-t border-gray-700 flex space-x-2">
            <input
              type="text"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Type your question..."
              className="flex-1 p-2 rounded border border-gray-700 bg-gray-900 text-white"
            />
            <button
              onClick={handleSendMessage}
              disabled={loading}
              className="bg-[#1DCD9F] text-black px-4 py-2 rounded transition"
            >
              {loading ? '...' : 'Send'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
