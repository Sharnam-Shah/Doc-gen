import React, { useState, useRef, useEffect } from 'react';
import { useParams, useNavigate, useLocation } from 'react-router-dom';
import { FileText, PenTool, Send, Download, User, Bot, Save, Edit, Eye, Bold, Italic, Strikethrough, Code, Pilcrow, Heading1, Heading2, Heading3, Indent as IndentIcon, Outdent as OutdentIcon, AlignLeft, AlignCenter, AlignRight, AlignJustify, Underline as UnderlineIcon, Minus as HorizontalRuleIcon, Share } from 'lucide-react';
import Comments from '../Components/ui/Comments';
import ShareDocument from '../Components/ui/ShareDocument';
import useWebSocket from '../lib/utils/useWebSocket';
import axios from '../api/axios';
import { saveAs } from 'file-saver';
import '../styles/MarkdownPreview.css';
import toast from 'react-hot-toast';
import DOMPurify from 'dompurify';

import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { Markdown } from 'tiptap-markdown';
import { Indent } from '../lib/tiptap-extensions/indent';
import TextAlign from '@tiptap/extension-text-align';
import Underline from '@tiptap/extension-underline';

import Image from '@tiptap/extension-image';

const MenuBar = ({ editor }) => {
  if (!editor) {
    return null;
  }

  return (
    <div className="flex items-center space-x-1 p-2 bg-gray-100 rounded-t-lg border-b border-gray-300">
      <button
        onClick={() => editor.chain().focus().toggleBold().run()}
        disabled={!editor.can().chain().focus().toggleBold().run()}
        className={editor.isActive('bold') ? 'is-active' : ''}
        title="Bold (Ctrl+B)"
      >
        <Bold className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleItalic().run()}
        disabled={!editor.can().chain().focus().toggleItalic().run()}
        className={editor.isActive('italic') ? 'is-active' : ''}
        title="Italic (Ctrl+I)"
      >
        <Italic className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleUnderline().run()}
        disabled={!editor.can().chain().focus().toggleUnderline().run()}
        className={editor.isActive('underline') ? 'is-active' : ''}
        title="Underline (Ctrl+U)"
      >
        <UnderlineIcon className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleStrike().run()}
        disabled={!editor.can().chain().focus().toggleStrike().run()}
        className={editor.isActive('strike') ? 'is-active' : ''}
        title="Strikethrough (Ctrl+Shift+X)"
      >
        <Strikethrough className="w-4 h-4" />
      </button>
      <div className="w-px h-5 bg-gray-300 mx-2"></div>
      <button
        onClick={() => editor.chain().focus().setParagraph().run()}
        className={editor.isActive('paragraph') ? 'is-active' : ''}
        title="Paragraph (Ctrl+Shift+0)"
      >
        <Pilcrow className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
        className={editor.isActive('heading', { level: 1 }) ? 'is-active' : ''}
        title="Heading 1 (Ctrl+Alt+1)"
      >
        <Heading1 className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
        className={editor.isActive('heading', { level: 2 }) ? 'is-active' : ''}
        title="Heading 2 (Ctrl+Alt+2)"
      >
        <Heading2 className="w-4 h-4" />
      </button>
      <button
        onClick={() => editor.chain().focus().toggleHeading({ level: 3 }).run()}
        className={editor.isActive('heading', { level: 3 }) ? 'is-active' : ''}
        title="Heading 3 (Ctrl+Alt+3)"
      >
        <Heading3 className="w-4 h-4" />
      </button>
      <button onClick={() => editor.chain().focus().setHorizontalRule().run()} title="Horizontal Rule">
        <HorizontalRuleIcon className="w-4 h-4" />
      </button>
      <div className="w-px h-5 bg-gray-300 mx-2"></div>
      <button onClick={() => editor.commands.indent()} title="Indent Paragraph">
        <IndentIcon className="w-4 h-4" />
      </button>
      <button onClick={() => editor.commands.outdent()} title="Outdent Paragraph">
        <OutdentIcon className="w-4 h-4" />
      </button>
      <div className="w-px h-5 bg-gray-300 mx-2"></div>
      <button onClick={() => editor.chain().focus().setTextAlign('left').run()} className={editor.isActive({ textAlign: 'left' }) ? 'is-active' : ''} title="Align Left">
        <AlignLeft className="w-4 h-4" />
      </button>
      <button onClick={() => editor.chain().focus().setTextAlign('center').run()} className={editor.isActive({ textAlign: 'center' }) ? 'is-active' : ''} title="Align Center">
        <AlignCenter className="w-4 h-4" />
      </button>
      <button onClick={() => editor.chain().focus().setTextAlign('right').run()} className={editor.isActive({ textAlign: 'right' }) ? 'is-active' : ''} title="Align Right">
        <AlignRight className="w-4 h-4" />
      </button>
      <button onClick={() => editor.chain().focus().setTextAlign('justify').run()} className={editor.isActive({ textAlign: 'justify' }) ? 'is-active' : ''} title="Align Justify">
        <AlignJustify className="w-4 h-4" />
      </button>
    </div>
  );
};

const DocumentCreation = () => {
  const { id: mongoConversationId } = useParams(); // This is the MongoDB conversation ID
  const navigate = useNavigate();
  const location = useLocation();
  const queryParams = new URLSearchParams(location.search);
  const versionToLoad = queryParams.get('version');
  
  // Initialize WebSocket connection if we have a document ID
  const webSocket = useWebSocket(mongoConversationId);
  
  const [messages, setMessages] = useState([]);
  const [title, setTitle] = useState('');
  const [chatMessage, setChatMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [finalDocument, setFinalDocument] = useState(''); // Now stores HTML
  const [isEditing, setIsEditing] = useState(false);
  const fileInputRef = useRef(null);
  const [signatureRole, setSignatureRole] = useState(null); // 'landlord' | 'tenant'
  const chatContainerRef = useRef(null);

  const editor = useEditor({
    extensions: [StarterKit, Markdown, Image.configure({ inline: true }), Indent, TextAlign.configure({ types: ['heading', 'paragraph'] }), Underline],
    content: finalDocument,
    onUpdate: ({ editor }) => {
      setFinalDocument(editor.getHTML());
    },
    editorProps: {
      attributes: {
        class: 'markdown-preview',
      },
    },
  });

  const fetchConversation = async (idToFetch) => {
    console.log("[DEBUG Frontend] fetchConversation called with ID:", idToFetch);
    if (idToFetch) {
      try {
        const convResponse = await axios.get(`conversations/${idToFetch}/`);
        const conversation = convResponse.data;
        console.log("[DEBUG Frontend] Fetched conversation messages:", conversation.messages);
        setTitle(conversation.title || '');
        setMessages(conversation.messages || []);
        
        if (conversation.document_versions && conversation.document_versions.length > 0) {
          let contentToLoad = '';
          if (versionToLoad) {
            const specificVersion = conversation.document_versions.find(v => v.version_number === parseInt(versionToLoad));
            if (specificVersion) {
              contentToLoad = specificVersion.content;
            } else {
              toast.error(`Version ${versionToLoad} not found.`);
              contentToLoad = conversation.document_versions[conversation.document_versions.length - 1].content; // Fallback to latest
            }
          } else {
            contentToLoad = conversation.document_versions[conversation.document_versions.length - 1].content; // Default to latest
          }
          setFinalDocument(contentToLoad);
        } else {
          setFinalDocument(''); // Clear document if no versions
        }
      } catch (error) {
        console.error('Error fetching conversation:', error);
        toast.error('Could not load conversation.');
      }
    } else {
      // Reset state for new document creation
      console.log("[DEBUG Frontend] Resetting state for new document creation.");
      setTitle('');
      setMessages([]);
      setFinalDocument('');
    }
  };

  useEffect(() => {
    if (editor && finalDocument !== editor.getHTML()) {
      // AI provides markdown, so we set it as such. onUpdate will convert it to HTML.
      editor.chain().setContent(finalDocument, false).setMeta('addToHistory', false).run();
    }
  }, [finalDocument, editor]);

  useEffect(() => {
    fetchConversation(mongoConversationId);
  }, [mongoConversationId, versionToLoad]); // Re-fetch when ID or version changes

  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSendMessage = async () => {
    if (!chatMessage.trim() || !editor) return;

    const userMessage = { sender: 'user', text: chatMessage, type: 'display' };
    setMessages(prev => [...prev, userMessage]);
    setChatMessage('');
    setIsGenerating(true);

    let payloadMessages = [...messages, userMessage];

    // If a document exists, get its markdown version for the AI context
    if (editor.getText()) {
      const markdownContext = editor.storage.markdown.getMarkdown();
      payloadMessages = [
        { sender: 'user', text: `Here is the legal document we are working on. Please use this as the basis for any updates.\n\n---\n\n${markdownContext}` },
        { sender: 'bot', text: 'Okay, I have the document. What changes would you like to make?' },
        userMessage
      ];
    }

    try {
      const response = await axios.post('chat/', { messages: payloadMessages });
      const aiResponse = response.data;
      
      if (aiResponse.type === 'document') {
        const documentMarkdown = aiResponse.text;
        // Set the new markdown content in the editor. The onUpdate handler will convert and save it to HTML.
        editor.chain().setContent(documentMarkdown).selectAll().indent().run();

        const newBotMessages = [
          { sender: 'bot', type: 'document_context', text: documentMarkdown },
          { sender: 'bot', type: 'display', text: "I have updated the document for you. You can review the changes and ask for more updates if needed." }
        ];
        setMessages(prev => [...prev, ...newBotMessages]);

      } else {
        setMessages(prev => [...prev, { sender: 'bot', type: 'display', text: aiResponse.text }]);
      }

    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = error.response?.data?.error || 'An error occurred. Please try again.';
      setMessages(prev => [...prev, { sender: 'bot', type: 'display', text: `Error: ${errorMessage}` }]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleSaveConversation = async () => {
    if (!title.trim()) {
      toast.error('Please provide a title for the document.');
      return;
    }

    if (!finalDocument.trim()) {
      toast.error('Document content cannot be empty.');
      return;
    }

    const savePromise = new Promise(async (resolve, reject) => {
      try {
        let idToUseForFetch = mongoConversationId;
        
        if (!mongoConversationId) {
          // New document
          const payload = {
            title: title.trim(),
            messages: messages,
            initial_document_content: finalDocument
          };
          
          const convResponse = await axios.documentOperation(
            'conversations/',
            'post',
            payload
          );

          idToUseForFetch = convResponse.data.id;
          navigate(`/document-creation/${idToUseForFetch}`, { replace: true });
          resolve(convResponse.data.message || 'New document created successfully!');
        } else {
          // Update existing document
          const payload = {
            title: title.trim(),
            messages: messages,
            new_document_content: finalDocument
          };
          
          const updateResponse = await axios.documentOperation(
            `conversations/${mongoConversationId}/`,
            'put',
            payload
          );
          
          resolve(updateResponse.data.message || 'Document updated successfully!');
        }

        // Refresh the conversation data with retries
        let retries = 3;
        while (retries > 0) {
          try {
            await fetchConversation(idToUseForFetch);
            break;
          } catch (error) {
            retries--;
            if (retries === 0) throw error;
            await new Promise(r => setTimeout(r, 1000)); // Wait 1 second before retry
          }
        }
      } catch (error) {
        console.error('Save error:', error);
        if (error.code === 'ECONNABORTED') {
          reject(new Error('Operation is taking longer than expected. Please try again.'));
        } else if (error.response?.status === 504) {
          reject(new Error('Server is busy. Please wait a moment and try again.'));
        } else if (error.response?.data?.error) {
          reject(new Error(error.response.data.error));
        } else if (!navigator.onLine) {
          reject(new Error('No internet connection. Please check your network.'));
        } else {
          reject(new Error('Unable to save document. Please try again.'));
        }
      }
    });

    toast.promise(savePromise, {
      loading: 'Saving document...',
      success: (message) => message,
      error: (error) => error.message
    });
  };

  const handleDownloadPdf = async () => {
    if (!mongoConversationId) {
      toast.error('Please save the document first.');
      return;
    }
    try {
      toast.loading('Generating PDF...');
      const response = await axios.get(`conversations/${mongoConversationId}/download/`, {
        responseType: 'blob',
        timeout: 60000, // Increased timeout for PDF generation
        headers: {
          'Accept': 'application/pdf'
        }
      });

      if (response.data.type === 'application/json') {
        // If we got JSON instead of a PDF, it's an error
        const reader = new FileReader();
        reader.onload = () => {
          const error = JSON.parse(reader.result);
          toast.error(error.message || 'Failed to generate PDF');
        };
        reader.readAsText(response.data);
        return;
      }

      const filename = `${title || 'legal_document'}_${new Date().toISOString().split('T')[0]}.pdf`;
      saveAs(response.data, filename);
      toast.success('PDF downloaded successfully!');
    } catch (error) {
      console.error('Error downloading PDF:', error);
      toast.error(error.message || 'Failed to download PDF. Please try again.');
    } finally {
      toast.dismiss();
    }
  };

  const handleSelectSignature = async (role) => {
    setSignatureRole(role);
    if (fileInputRef.current) fileInputRef.current.click();
  };

  const handleSignatureFileChange = async (e) => {
    const file = e.target.files?.[0];
    if (!file || !editor) return;
    if (!['image/png','image/jpeg','image/jpg','image/webp'].includes(file.type)) {
      toast.error('Please select a PNG, JPG, or WEBP image.');
      return;
    }
    try {
      const form = new FormData();
      form.append('signature', file);
      const res = await axios.post('upload-signature/', form, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      const url = res.data?.url;
      if (!url) {
        toast.error('Upload failed. No URL returned.');
        return;
      }
      const role = signatureRole === 'landlord' ? 'landlord' : 'tenant';
      const signatureMarkdown = `![signature ${role}](${url})`;
      const instruction = `You are formatting a legal document. Insert and position the signature image for the ${role === 'landlord' ? 'First Party (Landlord)' : 'Second Party (Tenant)'} in the correct designated area so the final order is:
1) First Party signature
2) First Party name
3) Second Party signature
4) Second Party name
Use exactly this markdown image for the ${role === 'landlord' ? 'First Party' : 'Second Party'}: ${signatureMarkdown}
Preserve all existing content and headings. Return the entire updated document in JSON as {"type":"document","text":"...markdown..."}.`.replace(/\\/g, '\\\\');

      let payloadMessages = [...messages];
      if (editor.getText()) {
        const markdownContext = editor.storage.markdown.getMarkdown().replace(/\\/g, '\\\\');
        payloadMessages = [
          { sender: 'user', text: `Here is the legal document we are working on. Please use this as the basis for any updates.\n\n---\n\n${markdownContext}` },
          { sender: 'bot', text: 'Okay, I have the document. What changes would you like to make?' }
        ];
      }
      payloadMessages.push({ sender: 'user', text: instruction });

      setIsGenerating(true);
      const chatRes = await axios.post('chat/', { messages: payloadMessages });
      const aiResponse = chatRes.data;
      if (aiResponse.type === 'document') {
        const documentMarkdown = aiResponse.text;
        editor.commands.setContent(documentMarkdown);
        const newBotMessages = [
          { sender: 'bot', type: 'document_context', text: documentMarkdown },
          { sender: 'bot', type: 'display', text: 'I have updated the document with the signature placement.' }
        ];
        setMessages(prev => [...prev, ...newBotMessages]);
        toast.success('Signature placed and document formatted.');
      } else {
        setMessages(prev => [...prev, { sender: 'bot', type: 'display', text: aiResponse.text || 'AI responded. Please review the update.' }]);
        toast.success('AI responded. Please review the update.');
      }
    } catch (error) {
      console.error('Signature upload error:', error);
      const msg = error.response?.data?.error || 'Failed to upload signature.';
      toast.error(msg);
    } finally {
      setIsGenerating(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setSignatureRole(null);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <div className="bg-white rounded-2xl shadow-xl p-8 mb-8 text-center">
          <div className="flex items-center justify-center mb-4">
            <FileText className="w-10 h-10 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-gray-900">{mongoConversationId ? 'Edit Document' : 'Create New Document'}</h1>
          </div>
          <p className="text-xl text-gray-600">
            {mongoConversationId ? 'Continue editing your document' : 'Build your legal document from scratch with our AI assistant.'}
          </p>
        </div>

        {/* Save Conversation Section */}
        <div className="bg-white rounded-2xl shadow-xl p-6 mb-8 flex items-center space-x-4">
            <input 
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Enter document title..."
                className="flex-1 px-6 py-4 text-lg border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-600 outline-none"
            />
            <button
                onClick={handleSaveConversation}
                className="px-6 py-4 bg-purple-600 text-white rounded-xl hover:bg-purple-700 transition-colors flex items-center space-x-2"
            >
                <Save className="w-5 h-5" />
                <span>{mongoConversationId ? 'Save New Version' : 'Create & Save'}</span>
            </button>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-6">
          <div ref={chatContainerRef} className="h-96 overflow-y-auto mb-4 p-4 border border-gray-200 rounded-lg bg-gray-50">
            {messages.filter(msg => msg.type !== 'document_context').map((msg, index) => (
              <div key={index} className={`flex items-start gap-3 my-4 ${msg.sender === 'user' ? 'justify-end' : ''}`}>
                {msg.sender === 'bot' && <Bot className="w-6 h-6 text-blue-600 flex-shrink-0" />}
                <div className={`p-3 rounded-lg max-w-lg ${msg.sender === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'}`}>
                  <p style={{whiteSpace: 'pre-wrap'}}>{msg.text}</p>
                </div>
                {msg.sender === 'user' && <User className="w-6 h-6 text-gray-600 flex-shrink-0" />}
              </div>
            ))}
            {isGenerating && (
              <div className="flex items-start gap-3 my-4">
                <Bot className="w-6 h-6 text-blue-600 flex-shrink-0" />
                <div className="p-3 rounded-lg bg-gray-200 text-gray-800"><i>Typing...</i></div>
              </div>
            )}
          </div>

          <div className="flex space-x-4">
            <textarea
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Continue the conversation..."
              className="flex-1 px-6 py-4 text-lg border border-blue-200 rounded-xl focus:ring-2 focus:ring-blue-600 outline-none bg-blue-50 resize-none"
              rows={1}
              disabled={isGenerating}
            />
            <button
              onClick={handleSendMessage}
              disabled={isGenerating}
              className="px-6 py-4 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-colors flex items-center space-x-2"
            >
              <Send className="w-5 h-5" />
              <span>Send</span>
            </button>
          </div>
        </div>

        {finalDocument && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mt-8">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-2xl font-bold text-gray-900">Generated Document Preview</h2>
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="flex items-center space-x-1 px-3 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors duration-200"
              >
                {isEditing ? <Eye className="w-4 h-4 text-gray-600" /> : <Edit className="w-4 h-4 text-gray-600" />}
                <span className="text-sm text-gray-700">{isEditing ? 'Preview' : 'Edit'}</span>
              </button>
            </div>

            {isEditing ? (
              <div>
                <MenuBar editor={editor} />
                <EditorContent editor={editor} />
              </div>
            ) : (
              <div className="markdown-preview" dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(finalDocument) }} />
            )}

            <div className="mt-6 flex items-center justify-center gap-3 flex-wrap">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={handleSignatureFileChange}
                className="hidden"
              />
              <button
                onClick={() => handleSelectSignature('landlord')}
                className="px-5 py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors flex items-center gap-2"
              >
                <PenTool className="w-5 h-5" />
                <span>First Party Signature</span>
              </button>
              <button
                onClick={() => handleSelectSignature('tenant')}
                className="px-5 py-3 border border-gray-300 rounded-xl hover:bg-gray-50 transition-colors flex items-center gap-2"
              >
                <PenTool className="w-5 h-5" />
                <span>Second Party Signature</span>
              </button>
              <button
                onClick={handleDownloadPdf}
                className="bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 text-white font-semibold py-3 px-8 rounded-xl text-lg transition-all duration-200 transform hover:scale-105 flex items-center justify-center gap-2"
              >
                <Download className="w-6 h-6" />
                <span>Download as PDF</span>
              </button>
              <ShareDocument documentContent={finalDocument} title={title} />
            </div>
            
            {/* Comments Section */}
            <div className="mt-8">
              <Comments 
                documentId={mongoConversationId} 
                webSocket={webSocket} 
                user={localStorage.getItem('username') || 'Anonymous User'} 
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default DocumentCreation;