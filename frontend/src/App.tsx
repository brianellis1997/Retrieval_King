import React, { useState } from 'react';
import { FileUpload } from './components/FileUpload';
import { ChatInterface } from './components/ChatInterface';
import { DocumentManager } from './components/DocumentManager';
import './index.css';

function App() {
  const [isLoading, setIsLoading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState('');
  const [uploadError, setUploadError] = useState('');
  const [refreshDocuments, setRefreshDocuments] = useState(0);

  const handleUploadSuccess = (response: any) => {
    setUploadSuccess(`Document "${response.filename}" uploaded successfully!`);
    setRefreshDocuments((prev) => prev + 1);

    setTimeout(() => {
      setUploadSuccess('');
    }, 3000);
  };

  const handleUploadError = (error: string) => {
    setUploadError(`Upload error: ${error}`);

    setTimeout(() => {
      setUploadError('');
    }, 5000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <header className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">RK</span>
            </div>
            <h1 className="text-3xl font-bold text-gray-900">Retrieval King</h1>
          </div>
          <p className="text-gray-600">
            Advanced RAG application with OCR, embeddings, and intelligent retrieval
          </p>
        </header>

        {uploadSuccess && (
          <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-800">
            {uploadSuccess}
          </div>
        )}

        {uploadError && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {uploadError}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-8">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">Upload Documents</h2>
              <FileUpload
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
                isLoading={isLoading}
                setIsLoading={setIsLoading}
              />
              <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <p className="text-sm text-blue-900">
                  <strong>Tip:</strong> Upload PDFs, images, or office documents. The system will automatically extract text and process them for retrieval.
                </p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow" style={{ height: '500px' }}>
              <ChatInterface
                isLoading={isLoading}
                setIsLoading={setIsLoading}
              />
            </div>
          </div>

          <div className="lg:col-span-1">
            <DocumentManager
              isLoading={isLoading}
              setIsLoading={setIsLoading}
              refreshTrigger={refreshDocuments}
            />
          </div>
        </div>

        <footer className="mt-12 pt-8 border-t border-gray-200 text-center text-gray-600 text-sm">
          <p>
            Powered by DeepSeek-OCR, IBM Granite Embeddings, and LangGraph
          </p>
          <p className="mt-2">
            Built with FastAPI, React, and Vite
          </p>
        </footer>
      </div>
    </div>
  );
}

export default App;
