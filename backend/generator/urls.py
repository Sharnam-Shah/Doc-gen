from django.urls import path
from .views import chat, download_pdf, conversation_list, conversation_detail, download_conversation_pdf, upload_signature, rag_search, rag_fill

urlpatterns = [
    path('chat/', chat, name='chat'),
    path('download-pdf/', download_pdf, name='download_pdf'),
    path('upload-signature/', upload_signature, name='upload-signature'),
    path('conversations/', conversation_list, name='conversation-list'),
    path('conversations/<str:pk>/', conversation_detail, name='conversation-detail'),
    path('conversations/<str:pk>/download/', download_conversation_pdf, name='download-conversation-pdf'),
    # RAG endpoints
    path('rag/search/', rag_search, name='rag-search'),
    path('rag/fill/', rag_fill, name='rag-fill'),
]