import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from '../api/axios';
import { FileText, PlusCircle, Download, Trash2, Eye, Edit, Search } from 'lucide-react';
import toast from 'react-hot-toast';

const MyDocuments = () => {
  const [conversations, setConversations] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredConversations, setFilteredConversations] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    fetchConversations();
  }, []);

      useEffect(() => {
      const lowercasedSearchTerm = searchTerm.toLowerCase();
      const filtered = conversations.filter(conv => {
        const titleMatch = conv.title.toLowerCase().includes(lowercasedSearchTerm);
        return titleMatch;
      });
      setFilteredConversations(filtered);
    }, [searchTerm, conversations]);
  const fetchConversations = async () => {
    try {
      const response = await axios.get('documents/conversations/');
      setConversations(response.data);
    } catch (error) {
      console.error('Error fetching conversations:', error);
      toast.error('Failed to load documents.');
    }
  };

  const handleDeleteConversation = async (id) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await axios.delete(`documents/conversations/${id}/`);
        toast.success('Document deleted successfully!');
        fetchConversations(); // Refresh the list
      } catch (error) {
        console.error('Error deleting conversation:', error);
        toast.error('Failed to delete document.');
      }
    }
  };

  const handleDownloadLatestPdf = async (conversationId, title) => {
    try {
      const response = await axios.get(`utils/conversations/${conversationId}/download-latest-pdf/`, {
        responseType: 'blob', // Important for downloading files
      });
      const filename = `${title || 'document'}.pdf`;
      const blob = new Blob([response.data], { type: 'application/pdf' });
      saveAs(blob, filename);
      toast.success('Latest document PDF downloaded!');
    } catch (error) {
      console.error('Error downloading PDF:', error);
      toast.error('Failed to download PDF.');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 text-center">
          <div className="flex items-center justify-center mb-4">
            <FileText className="w-10 h-10 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">My Documents</h1>
          </div>
          <p className="text-xl text-gray-600">Manage your legal documents and their versions.</p>
        </div>

        <div className="flex justify-between items-center mb-6">
          <div className="relative flex-grow mr-4">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search documents by title or content..."
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 outline-none"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button
            onClick={() => navigate('/document-creation')}
            className="px-6 py-3 bg-green-600 text-white rounded-xl hover:bg-green-700 transition-colors flex items-center space-x-2 shadow-lg"
          >
            <PlusCircle className="w-5 h-5" />
            <span>Create New Document</span>
          </button>
        </div>

        {filteredConversations.length === 0 && conversations.length > 0 && (
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center text-gray-500 text-lg">
            No documents match your search.
          </div>
        )}

        {conversations.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-xl p-8 text-center text-gray-500 text-lg">
            You don't have any documents yet. Click "Create New Document" to get started!
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {filteredConversations.map((conv) => (
              <div key={conv._id} className="bg-white rounded-2xl shadow-xl p-6 flex flex-col justify-between border border-gray-200 hover:border-blue-400 transition-all duration-200">
                <div>
                  <h2 className="text-xl font-semibold text-gray-800 mb-2">{conv.title}</h2>
                  <p className="text-gray-500 text-sm mb-4">Created: {new Date(conv.created_at).toLocaleDateString()}</p>
                </div>
                <div className="flex justify-between items-center mt-4 space-x-2">
                  <button
                    onClick={() => navigate(`/document-creation/${conv._id}`)}
                    className="flex-1 px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors flex items-center justify-center space-x-2 text-sm"
                  >
                    <Edit className="w-4 h-4" />
                    <span>Edit</span>
                  </button>
                  <button
                    onClick={() => navigate(`/document-analyzer/${conv._id}`)}
                    className="flex-1 px-4 py-2 bg-purple-500 text-white rounded-lg hover:bg-purple-600 transition-colors flex items-center justify-center space-x-2 text-sm"
                  >
                    <Eye className="w-4 h-4" />
                    <span>View Versions</span>
                  </button>
                  <button
                    onClick={() => handleDownloadLatestPdf(conv._id, conv.title)}
                    className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors flex items-center justify-center space-x-2 text-sm"
                  >
                    <Download className="w-4 h-4" />
                    <span>PDF</span>
                  </button>
                  <button
                    onClick={() => handleDeleteConversation(conv._id)}
                    className="flex-1 px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-colors flex items-center justify-center space-x-2 text-sm"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Delete</span>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default MyDocuments;