import React, { useState } from 'react';
import { Share, Copy, Loader } from 'lucide-react';
import { documentAPI } from '../../api/documentAPI';
import toast from 'react-hot-toast';

const ShareDocument = ({ documentContent, title }) => {
    const [open, setOpen] = useState(false);
    const [shareUrl, setShareUrl] = useState('');
    const [snackbarOpen, setSnackbarOpen] = useState(false);
    const [isGenerating, setIsGenerating] = useState(false);

    const handleClickOpen = async () => {
        if (!documentContent) {
            toast.error('No document content to share');
            return;
        }

        setIsGenerating(true);
        let toastId = toast.loading('Generating share link...');

        try {
            const response = await documentAPI.shareDocument(documentContent, title);

            // Prefer returned id, fall back to share_url if available
            const docId = response?.id || (response?.share_url ? response.share_url.split('/').pop() : null);

            if (docId) {
                const baseUrl = window.location.origin;
                const shareUrl = `${baseUrl}/shared/${docId}`;
                setShareUrl(shareUrl);
                setOpen(true);
                toast.success('Share link generated successfully!', { id: toastId });
            } else {
                console.error('Unexpected share response', response);
                throw new Error('Failed to generate share link');
            }
            } catch (error) {
                console.error('Error generating share link:', error);
                toast.error(
                    error.response?.data?.error || 'Failed to generate share link. Please try again.',
                    { id: toastId }
                );
            } finally {
                setIsGenerating(false);
            }
    };

    const handleClose = () => {
        setOpen(false);
    };

    const handleCopyClick = () => {
        navigator.clipboard.writeText(shareUrl);
        setSnackbarOpen(true);
    };

    return (
        <>
            <button
                onClick={handleClickOpen}
                disabled={isGenerating}
                className={`px-6 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors flex items-center space-x-2 ${isGenerating ? 'opacity-75 cursor-not-allowed' : ''}`}
            >
                {isGenerating ? (
                    <>
                        <Loader className="w-5 h-5 animate-spin" />
                        <span>Generating Link...</span>
                    </>
                ) : (
                    <>
                        <Share className="w-5 h-5" />
                        <span>Share Document</span>
                    </>
                )}
            </button>
            
            {open && (
                <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl p-6 max-w-lg w-full mx-4">
                        <h2 className="text-2xl font-bold mb-4">Share Document</h2>
                        <div className="flex items-center space-x-2 mb-4">
                            <input
                                type="text"
                                value={shareUrl}
                                readOnly
                                className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
                            />
                            <button
                                onClick={handleCopyClick}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                                title="Copy to clipboard"
                            >
                                <Copy className="w-5 h-5" />
                            </button>
                        </div>
                        <div className="flex justify-end">
                            <button
                                onClick={handleClose}
                                className="px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300 transition-colors"
                            >
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
};

export default ShareDocument;