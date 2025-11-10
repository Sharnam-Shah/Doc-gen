import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from '../api/axios';
import Comments from '../Components/ui/Comments';
import useWebSocket from '../lib/utils/useWebSocket';
import '../styles/MarkdownPreview.css';
import DOMPurify from 'dompurify';
import { FileText } from 'lucide-react';
import toast from 'react-hot-toast';

const SharedDocument = () => {
    const { id } = useParams();
    const [document, setDocument] = useState(null);
    const [loading, setLoading] = useState(true);
    const webSocket = useWebSocket(id);

    useEffect(() => {
        const fetchDocument = async () => {
            try {
                const response = await axios.get(`conversations/${id}/`);
                if (response.data && response.data.document_versions && response.data.document_versions.length > 0) {
                    setDocument({
                        title: response.data.title,
                        content: response.data.document_versions[response.data.document_versions.length - 1].content
                    });
                }
                setLoading(false);
            } catch (error) {
                console.error('Error fetching document:', error);
                toast.error('Failed to load document');
                setLoading(false);
            }
        };

        fetchDocument();
    }, [id]);

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8 flex items-center justify-center">
                <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600"></div>
            </div>
        );
    }

    if (!document) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
                <div className="max-w-4xl mx-auto px-4 text-center">
                    <h1 className="text-2xl font-bold text-gray-800 mb-4">Document not found</h1>
                    <p className="text-gray-600">This document may have been removed or you don't have permission to view it.</p>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
            <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
                <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 text-center">
                    <div className="flex items-center justify-center mb-4">
                        <FileText className="w-10 h-10 text-blue-600 mr-3" />
                        <h1 className="text-4xl font-bold text-gray-900">{document.title}</h1>
                    </div>
                </div>

                <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
                    <div 
                        className="markdown-preview"
                        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(document.content) }}
                    />
                </div>

                <div className="bg-white rounded-2xl shadow-xl p-8">
                    <Comments 
                        documentId={id}
                        webSocket={webSocket}
                        user={localStorage.getItem('username') || 'Anonymous User'}
                    />
                </div>
            </div>
        </div>
    );
};

export default SharedDocument;