from django.urls import path
from . import views

urlpatterns = [
    path('download-pdf/', views.download_pdf, name='download-pdf'),
    path('upload-signature/', views.upload_signature, name='upload-signature'),
    path('conversations/<str:pk>/download-latest-pdf/', views.download_latest_conversation_pdf, name='download-latest-conversation-pdf'),
    path('conversations/<str:pk>/versions/<int:version_number>/download-pdf/', views.download_version_pdf, name='download-version-pdf'),
]
