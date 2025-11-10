import React, { useState, useEffect, useCallback, useRef } from 'react';
import { Send, User, Loader } from 'lucide-react';
import axios from '../../api/axios';
import toast from 'react-hot-toast';

const Comments = ({ documentId, webSocket, user }) => {
    const [comments, setComments] = useState([]);
    const [newComment, setNewComment] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [isLoading, setIsLoading] = useState(true);
    const commentsEndRef = useRef(null);
    const prevMessagesLenRef = useRef(0);
    const listenerCleanupRef = useRef(null);

    const scrollToBottom = () => {
        commentsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        // Fetch existing comments
        const fetchComments = async () => {
            try {
                const response = await axios.get(`/documents/${documentId}/comments/`);
                setComments(response.data);
            } catch (error) {
                console.error('Error fetching comments:', error);
                toast.error('Failed to load comments');
            } finally {
                setIsLoading(false);
            }
        };
        if (documentId) {
            fetchComments();
        }
    }, [documentId]);

    useEffect(() => {
        // Scroll to bottom when new comments are added
        scrollToBottom();
    }, [comments]);

    useEffect(() => {
        // Register a direct listener with the WebSocket hook so we get
        // incoming comment events immediately. This avoids relying on
        // array-length diffs and prevents races where messages are missed.
        if (!webSocket || typeof webSocket.addListener !== 'function') return;

        const onMessage = (message) => {
            if (message.type === 'comment' && message.comment) {
                const incoming = message.comment;

                setComments(prev => {
                    // If we optimistically added a temporary comment with a
                    // tmp- id that matches content+user, remove it before
                    // appending the persisted one to avoid duplicates.
                    const filtered = prev.filter(c => {
                        if ((c.id || '').toString().startsWith('tmp-') && c.user === incoming.user && c.content === incoming.content) {
                            return false; // drop optimistic
                        }
                        return true;
                    });
                    return [...filtered, incoming];
                });
            }
        };

        // addListener returns a cleanup function in the hook; keep it
        listenerCleanupRef.current = webSocket.addListener(onMessage);
        return () => {
            if (typeof listenerCleanupRef.current === 'function') {
                listenerCleanupRef.current();
            }
        };
    }, [webSocket]);

    const handleSubmitComment = useCallback(async () => {
        if (!newComment.trim() || isSubmitting) return;

        setIsSubmitting(true);
        try {
            webSocket.sendMessage('comment', {
                user: user,
                content: newComment.trim()
            });

            // optimistic local comment with temporary id (will be replaced
            // when the server echoes the persisted comment)
            const tempComment = {
                id: `tmp-${Date.now()}`,
                user: user,
                content: newComment.trim(),
                created_at: new Date().toISOString()
            };
            setComments(prev => [...prev, tempComment]);
            setNewComment('');
        } catch (error) {
            console.error('Error sending comment:', error);
            toast.error('Failed to send comment');
        } finally {
            setIsSubmitting(false);
        }
    }, [newComment, user, webSocket, isSubmitting]);

    return (
        <div className="bg-white rounded-xl shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4">Comments</h2>
            {isLoading ? (
                <div className="flex justify-center items-center h-32">
                    <Loader className="w-8 h-8 animate-spin text-blue-600" />
                </div>
            ) : (
                <>
                    <div className="max-h-[300px] overflow-y-auto mb-4 space-y-4">
                        {comments.length === 0 ? (
                            <div className="text-center text-gray-500 py-8">
                                No comments yet. Be the first to comment!
                            </div>
                        ) : (
                            comments.map((comment, index) => (
                                <div key={comment.id || index} className="bg-gray-50 rounded-lg p-4 shadow-sm">
                                    <div className="flex items-center space-x-2 mb-2">
                                        <div className="bg-blue-100 rounded-full p-1">
                                            <User className="w-4 h-4 text-blue-600" />
                                        </div>
                                        <span className="font-medium text-gray-900">{comment.user}</span>
                                        <span className="text-sm text-gray-500">
                                            {new Date(comment.created_at).toLocaleString()}
                                        </span>
                                    </div>
                                    <p className="text-gray-700">{comment.content}</p>
                                </div>
                            ))
                        )}
                        <div ref={commentsEndRef} />
                    </div>
                    <div className="flex items-center space-x-4">
                        <input
                            type="text"
                            placeholder="Add a comment..."
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            onKeyPress={(e) => {
                                if (e.key === 'Enter' && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSubmitComment();
                                }
                            }}
                            disabled={isSubmitting}
                            className={`flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none ${
                                isSubmitting ? 'bg-gray-100' : ''
                            }`}
                        />
                        <button
                            onClick={handleSubmitComment}
                            disabled={isSubmitting || !newComment.trim()}
                            className={`px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center space-x-2 ${
                                (isSubmitting || !newComment.trim()) ? 'opacity-50 cursor-not-allowed' : ''
                            }`}
                        >
                            {isSubmitting ? (
                                <Loader className="w-4 h-4 animate-spin" />
                            ) : (
                                <Send className="w-4 h-4" />
                            )}
                            <span>{isSubmitting ? 'Sending...' : 'Send'}</span>
                        </button>
                    </div>
                </>
            )}
        </div>
    );
};

export default Comments;