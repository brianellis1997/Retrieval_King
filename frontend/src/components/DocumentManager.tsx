import React, { useState, useEffect } from 'react';
import { apiService, Document } from '../services/api';

interface DocumentManagerProps {
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  refreshTrigger: number;
}

export const DocumentManager: React.FC<DocumentManagerProps> = ({
  isLoading,
  setIsLoading,
  refreshTrigger,
}) => {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDocuments();
  }, [refreshTrigger]);

  const loadDocuments = async () => {
    try {
      setIsLoading(true);
      setError('');
      const docs = await apiService.listDocuments();
      setDocuments(docs);
    } catch (err: any) {
      setError(err.message || 'Failed to load documents');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (documentId: string, filename: string) => {
    if (!window.confirm(`Delete "${filename}"?`)) {
      return;
    }

    try {
      setIsLoading(true);
      await apiService.deleteDocument(documentId);
      setDocuments((prev) => prev.filter((doc) => doc.id !== documentId));
    } catch (err: any) {
      setError(err.message || 'Failed to delete document');
    } finally {
      setIsLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
  };

  const formatDate = (dateString: string): string => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-6 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Documents</h2>
        <p className="text-sm text-gray-600 mt-1">
          {documents.length} document{documents.length !== 1 ? 's' : ''} uploaded
        </p>
      </div>

      {error && (
        <div className="p-4 m-4 bg-red-50 border border-red-200 rounded-lg text-red-800 text-sm">
          {error}
        </div>
      )}

      {documents.length === 0 ? (
        <div className="p-6 text-center text-gray-500">
          <p>No documents uploaded yet</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50">
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Name</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Type</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Size</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Chunks</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Uploaded</th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700">Actions</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-6 py-4 text-sm font-medium text-gray-900">{doc.filename}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{doc.file_type}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{formatFileSize(doc.file_size)}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{doc.num_chunks}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">{formatDate(doc.upload_time)}</td>
                  <td className="px-6 py-4 text-sm">
                    <button
                      onClick={() => handleDelete(doc.id, doc.filename)}
                      disabled={isLoading}
                      className="text-red-600 hover:text-red-800 disabled:text-gray-400 disabled:cursor-not-allowed font-medium transition-colors"
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
