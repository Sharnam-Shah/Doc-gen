from rest_framework import serializers
from .models import DocumentComment

class DocumentCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentComment
        fields = ['id', 'document_id', 'user', 'content', 'position', 'created_at', 'parent_comment_id']
        read_only_fields = ['id', 'user', 'created_at']