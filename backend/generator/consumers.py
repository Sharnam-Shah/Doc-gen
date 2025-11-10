import json
from datetime import datetime
from bson import ObjectId
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import DocumentComment
from .mongo_client import get_conversation_by_id, update_conversation, save_conversation

def json_serializer(obj):
    """Custom JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, ObjectId):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")

class DocumentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.document_id = self.scope['url_route']['kwargs']['document_id']
        self.room_group_name = f'document_{self.document_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

        # Send initial document data if it exists
        if self.document_id != 'undefined':
            document = await self.get_document()
            if document:
                await self.send(text_data=json.dumps({
                    'type': 'document_state',
                    'document': document
                }, default=json_serializer))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            print(f"[WebSocket] Received message type: {message_type}, data: {data}")

            if message_type == 'share_document':
                # Handle document sharing
                document_data = {
                    'title': data.get('title', 'Shared Document'),
                    'content': data.get('content'),
                    'messages': [],
                    'initial_document_content': data.get('content'),
                    'notes': 'Shared document',
                }
                
                document_id = await self.save_document(document_data)
                
                # Send success response back to the sender
                await self.send(text_data=json.dumps({
                    'type': 'share_success',
                    'document_id': str(document_id)
                }, default=json_serializer))

            elif message_type == 'update_document':
                # Handle document updates
                success = await self.update_document(data)
                if success:
                    # Broadcast to all connected clients except sender
                    await self.channel_layer.group_send(
                        self.room_group_name,
                        {
                            'type': 'document_update',
                            'content': data.get('content')
                        }
                    )

            elif message_type == 'comment':
                # Handle new comment
                print(f"[WebSocket] Processing comment from user: {data.get('user')}")
                comment = await self.save_comment(
                    user=data['user'],
                    content=data['content'],
                    position=data.get('position'),
                    parent_comment_id=data.get('parent_comment_id')
                )
                print(f"[WebSocket] Comment saved with ID: {comment.id}")
                
                # Broadcast comment to group
                comment_data = {
                    'type': 'comment_message',
                    'comment': {
                        'id': comment.id,
                        'user': comment.user,
                        'content': comment.content,
                        'position': comment.position,
                        'created_at': comment.created_at.isoformat(),
                        'parent_comment_id': comment.parent_comment_id if comment.parent_comment else None
                    }
                }
                print(f"[WebSocket] Broadcasting comment to group: {self.room_group_name}")
                await self.channel_layer.group_send(
                    self.room_group_name,
                    comment_data
                )

            elif message_type == 'suggestion':
                # Handle document edit suggestion
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'suggestion_message',
                        'suggestion': {
                            'user': data['user'],
                            'content': data['content'],
                            'position': data.get('position', {})
                        }
                    }
                )

        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }, default=json_serializer))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }, default=json_serializer))

    async def comment_message(self, event):
        # Send comment to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'comment',
            'comment': event['comment']
        }, default=json_serializer))

    async def suggestion_message(self, event):
        # Send suggestion to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'suggestion',
            'suggestion': event['suggestion']
        }, default=json_serializer))

    async def document_update(self, event):
        # Send document update to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'document_update',
            'content': event['content']
        }, default=json_serializer))

    @database_sync_to_async
    def get_document(self):
        if self.document_id == 'undefined':
            return None
        return get_conversation_by_id(self.document_id)

    @database_sync_to_async
    def save_document(self, document_data):
        return save_conversation(
            title=document_data['title'],
            messages=document_data['messages'],
            initial_document_content=document_data['initial_document_content'],
            notes=document_data['notes']
        )

    @database_sync_to_async
    def update_document(self, data):
        return update_conversation(
            self.document_id,
            data.get('title'),
            data.get('messages', []),
            data.get('content'),
            notes='Document updated via WebSocket'
        )

    @database_sync_to_async
    def save_comment(self, user, content, position=None, parent_comment_id=None):
        parent_comment = None
        if parent_comment_id:
            parent_comment = DocumentComment.objects.get(id=parent_comment_id)
        
        comment = DocumentComment.objects.create(
            document_id=self.document_id,
            user=user,
            content=content,
            position=position,
            parent_comment=parent_comment
        )
        return comment