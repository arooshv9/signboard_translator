  // src/TranslationHistory.js - Component for viewing translation history
  import React, { useState, useEffect } from 'react';
  import { 
    History, 
    Trash2, 
    Eye, 
    Clock, 
    FileText, 
    Globe, 
    BarChart3,
    RefreshCw,
    AlertCircle,
    Calendar,
    Image as ImageIcon,
    X
  } from 'lucide-react';

  const TranslationHistory = ({ isOpen, onClose }) => {
    const [history, setHistory] = useState([]);
    const [stats, setStats] = useState(null);
    const [selectedTranslation, setSelectedTranslation] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [error, setError] = useState('');

    // Fetch history when component opens
    useEffect(() => {
      if (isOpen) {
        fetchHistory();
        fetchStats();
      }
    }, [isOpen, currentPage]);

    const fetchHistory = async () => {
      setIsLoading(true);
      setError('');
      
      try {
        const response = await fetch(`http://localhost:5000/api/history?page=${currentPage}&per_page=10`, {
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Failed to fetch history');
        }
        
        const data = await response.json();
        setHistory(data.translations);
        setTotalPages(data.pages);
      } catch (err) {
        setError('Failed to load translation history');
        console.error('History fetch error:', err);
      } finally {
        setIsLoading(false);
      }
    };

    const fetchStats = async () => {
      try {
        const response = await fetch('http://localhost:5000/api/stats', {
          credentials: 'include'
        });
        
        if (response.ok) {
          const data = await response.json();
          setStats(data);
        }
      } catch (err) {
        console.error('Stats fetch error:', err);
      }
    };

    const deleteTranslation = async (translationId) => {
      if (!window.confirm('Are you sure you want to delete this translation?')) return;
      
      try {
        const response = await fetch(`http://localhost:5000/api/history/${translationId}`, {
          method: 'DELETE',
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Failed to delete translation');
        }
        
        // Refresh history after deletion
        fetchHistory();
        fetchStats();
        setSelectedTranslation(null);
      } catch (err) {
        setError('Failed to delete translation');
        console.error('Delete error:', err);
      }
    };

    const clearAllHistory = async () => {
      if (!window.confirm('Are you sure you want to clear all translation history? This cannot be undone.')) return;
      
      try {
        const response = await fetch('http://localhost:5000/api/history/clear', {
          method: 'DELETE',
          credentials: 'include'
        });
        
        if (!response.ok) {
          throw new Error('Failed to clear history');
        }
        
        setHistory([]);
        setStats(null);
        setSelectedTranslation(null);
        fetchStats();
      } catch (err) {
        setError('Failed to clear history');
        console.error('Clear error:', err);
      }
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString();
    };

    const formatFileSize = (bytes) => {
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      if (bytes === 0) return '0 Bytes';
      const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
      return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
    };

    if (!isOpen) return null;

    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-xl shadow-2xl w-full max-w-6xl h-5/6 flex flex-col">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center">
              <History className="w-6 h-6 text-indigo-600 mr-2" />
              <h2 className="text-2xl font-semibold text-gray-800">Translation History</h2>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={fetchHistory}
                className="p-2 text-gray-500 hover:text-indigo-600 transition-colors"
                title="Refresh"
              >
                <RefreshCw className="w-5 h-5" />
              </button>
              {history.length > 0 && (
                <button
                  onClick={clearAllHistory}
                  className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                >
                  Clear All
                </button>
              )}
              <button
                onClick={onClose}
                className="p-2 text-gray-500 hover:text-gray-700 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          <div className="flex-1 flex overflow-hidden">
            {/* Left Panel - History List */}
            <div className="w-1/2 border-r border-gray-200 flex flex-col">
              {/* Stats */}
              {stats && (
                <div className="p-4 bg-gray-50 border-b border-gray-200">
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center">
                      <BarChart3 className="w-4 h-4 text-indigo-600 mr-2" />
                      <span>{stats.total_translations} translations</span>
                    </div>
                    <div className="flex items-center">
                      <Clock className="w-4 h-4 text-green-600 mr-2" />
                      <span>{stats.average_processing_time}s avg</span>
                    </div>
                  </div>
                </div>
              )}

              {/* History List */}
              <div className="flex-1 overflow-y-auto">
                {isLoading ? (
                  <div className="flex items-center justify-center p-8">
                    <RefreshCw className="w-6 h-6 animate-spin text-indigo-600" />
                  </div>
                ) : history.length === 0 ? (
                  <div className="text-center p-8">
                    <FileText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">No translation history yet</p>
                  </div>
                ) : (
                  <div className="space-y-2 p-4">
                    {history.map((translation) => (
                      <div
                        key={translation.id}
                        className={`p-3 rounded-lg cursor-pointer transition-colors ${
                          selectedTranslation?.id === translation.id
                            ? 'bg-indigo-50 border border-indigo-200'
                            : 'hover:bg-gray-50 border border-transparent'
                        }`}
                        onClick={() => setSelectedTranslation(translation)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center">
                            <ImageIcon className="w-4 h-4 text-gray-400 mr-2" />
                            <span className="font-medium text-sm truncate">
                              {translation.original_filename}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {formatFileSize(translation.image_size)}
                          </span>
                        </div>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-gray-500">
                            {translation.original_texts.length} texts found
                          </span>
                          <span className="text-xs text-gray-500">
                            {formatDate(translation.created_at).split(',')[0]}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="p-4 border-t border-gray-200 flex justify-center">
                  <div className="flex gap-2">
                    <button
                      onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                      disabled={currentPage === 1}
                      className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                    >
                      Previous
                    </button>
                    <span className="px-3 py-1 text-sm">
                      {currentPage} of {totalPages}
                    </span>
                    <button
                      onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                      disabled={currentPage === totalPages}
                      className="px-3 py-1 text-sm border rounded disabled:opacity-50"
                    >
                      Next
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Right Panel - Translation Details */}
            <div className="w-1/2 flex flex-col">
              {selectedTranslation ? (
                <div className="flex-1 overflow-y-auto p-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-lg font-semibold text-gray-800">
                      Translation Details
                    </h3>
                    <button
                      onClick={() => deleteTranslation(selectedTranslation.id)}
                      className="p-2 text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      title="Delete Translation"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="text-sm font-medium text-gray-600">File Name:</label>
                      <p className="text-gray-800">{selectedTranslation.original_filename}</p>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="text-sm font-medium text-gray-600">File Size:</label>
                        <p className="text-gray-800">{formatFileSize(selectedTranslation.image_size)}</p>
                      </div>
                      <div>
                        <label className="text-sm font-medium text-gray-600">Dimensions:</label>
                        <p className="text-gray-800">{selectedTranslation.image_dimensions}</p>
                      </div>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-gray-600">Processing Time:</label>
                      <p className="text-gray-800">{selectedTranslation.processing_time}s</p>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-gray-600">Created:</label>
                      <p className="text-gray-800">{formatDate(selectedTranslation.created_at)}</p>
                    </div>

                    <div>
                      <label className="text-sm font-medium text-gray-600">Translations:</label>
                      <div className="space-y-3 mt-2">
                        {selectedTranslation.original_texts.map((originalText, index) => (
                          <div key={index} className="p-3 border border-gray-200 rounded-lg">
                            <div className="text-sm text-gray-600 mb-1">Original:</div>
                            <div className="font-medium text-gray-800 mb-2">{originalText}</div>
                            <div className="text-sm text-gray-600 mb-1">English Translation:</div>
                            <div className="text-green-700 font-medium">
                              {selectedTranslation.translated_texts[index]}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center">
                    <Eye className="w-12 h-12 text-gray-300 mx-auto mb-3" />
                    <p className="text-gray-500">Select a translation to view details</p>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="p-4 bg-red-50 border-t border-red-200 flex items-center">
              <AlertCircle className="w-5 h-5 text-red-500 mr-2" />
              <span className="text-red-700">{error}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  export default TranslationHistory;