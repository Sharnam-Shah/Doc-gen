from django.urls import path
from .views import (
    chat, download_pdf, conversation_list, conversation_detail, 
    download_latest_conversation_pdf, upload_signature, get_version_content, 
    download_version_pdf, generate_share_link, document_comments
)

urlpatterns = [

    path('chat/', chat, name='chat'),
    path('download-pdf/', download_pdf, name='download_pdf'), # This is for download_pdf from markdown string
    path('upload-signature/', upload_signature, name='upload-signature'),
    path('conversations/', conversation_list, name='conversation-list'),
    path('conversations/<str:pk>/', conversation_detail, name='conversation-detail'),
    path('conversations/<str:pk>/download/', download_latest_conversation_pdf, name='download-latest-conversation-pdf'),
    path('conversations/<str:pk>/versions/<int:version_number>/content/', get_version_content, name='get-version-content'),
    path('conversations/<str:pk>/versions/<int:version_number>/download/', download_version_pdf, name='download-version-pdf'),
    path('share/', generate_share_link, name='generate-share-link'),
    path('documents/<str:document_id>/comments/', document_comments, name='document-comments'),
]
