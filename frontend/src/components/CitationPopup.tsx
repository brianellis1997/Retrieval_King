import React, { useEffect } from 'react';
import { Citation } from '../services/api';

interface CitationPopupProps {
  citation: Citation;
  onClose: () => void;
}

export const CitationPopup: React.FC<CitationPopupProps> = ({ citation, onClose }) => {
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-2xl max-h-96 overflow-y-auto p-6"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-start mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Citation #{citation.citation_id}</h3>
            <p className="text-sm text-gray-600 mt-1">{citation.filename}</p>
            {citation.page_number && (
              <p className="text-sm text-gray-600">Page {citation.page_number}</p>
            )}
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-xl font-semibold"
          >
            ×
          </button>
        </div>

        <div className="mb-4">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs font-semibold text-gray-600 uppercase">Confidence</span>
            <div className="flex-1 h-2 bg-gray-200 rounded-full">
              <div
                className="h-2 bg-blue-600 rounded-full"
                style={{ width: `${citation.confidence_score * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-600">{(citation.confidence_score * 100).toFixed(0)}%</span>
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
          <p className="text-gray-700 text-sm leading-relaxed whitespace-pre-wrap">
            {citation.text}
          </p>
        </div>

        <div className="mt-4 text-xs text-gray-500 space-y-1">
          <p>Chunk ID: <code className="bg-gray-100 px-2 py-1 rounded">{citation.chunk_id}</code></p>
          <p>Document ID: <code className="bg-gray-100 px-2 py-1 rounded">{citation.document_id}</code></p>
        </div>
      </div>
    </div>
  );
};
