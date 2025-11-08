from django.urls import path
from . import views

urlpatterns = [
    path('conversations/', views.conversation_list, name='conversation-list'),
    path('conversations/<str:pk>/', views.conversation_detail, name='conversation-detail'),
    path('conversations/<str:pk>/versions/<int:version_number>/content/', views.get_version_content, name='get-version-content'),
]
