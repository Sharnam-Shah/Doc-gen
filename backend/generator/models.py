from django.db import models
from django.utils import timezone

class DocumentComment(models.Model):
    document_id = models.CharField(max_length=255)  # MongoDB document ID
    user = models.CharField(max_length=255)  # User identifier
    content = models.TextField()  # Comment content
    position = models.JSONField(null=True)  # Position in the document (optional)
    created_at = models.DateTimeField(default=timezone.now)
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)  # For threaded comments

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.user} on document {self.document_id}"
