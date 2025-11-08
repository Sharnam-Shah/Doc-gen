from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from documents.mongo_client import get_all_conversations, get_conversation_by_id, save_conversation, update_conversation, delete_conversation, get_document_version_content


@api_view(['GET', 'POST'])
def conversation_list(request):
    """
    List all conversations or create a new one.
    """
    if request.method == 'GET':
        conversations = get_all_conversations()
        return Response(conversations)

    elif request.method == 'POST':
        title = request.data.get('title')
        messages = request.data.get('messages')
        initial_document_content = request.data.get('initial_document_content')
        notes = request.data.get('notes', 'Initial Version')

        print(f"[DEBUG Backend] conversation_list (POST) - Received messages: {messages}")

        if not title or not messages:
            return Response({'error': 'Title and messages are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        conversation_id = save_conversation(title, messages, initial_document_content, uploaded_by=(request.user.username if request.user.is_authenticated else 'anonymous'), notes=notes)
        if conversation_id:
            return Response({'id': conversation_id}, status=status.HTTP_201_CREATED)
        else:
            return Response({'error': 'Failed to save conversation'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'PUT', 'DELETE'])
def conversation_detail(request, pk):
    """
    Retrieve, update or delete a single conversation.
    """
    if request.method == 'GET':
        conversation = get_conversation_by_id(pk)
        if conversation:
            return Response(conversation)
        else:
            return Response({'error': 'Conversation not found'}, status=status.HTTP_404_NOT_FOUND)
    
    elif request.method == 'PUT':
        title = request.data.get('title')
        messages = request.data.get('messages')
        new_document_content = request.data.get('new_document_content')
        notes = request.data.get('notes', f'Version update via AI editor')

        print(f"[DEBUG Backend] conversation_detail (PUT) - Received messages: {messages}")

        if not title or not messages:
            return Response({'error': 'Title and messages are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        success = update_conversation(pk, title, messages, new_document_content, uploaded_by=(request.user.username if request.user.is_authenticated else 'anonymous'), notes=notes)
        if success:
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'Failed to update conversation'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'DELETE':
        success = delete_conversation(pk)
        if success:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response({'error': 'Failed to delete conversation'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_version_content(request, pk, version_number):
    """
    Retrieves the content of a specific document version from a conversation.
    """
    try:
        conversation = get_conversation_by_id(pk)
        if not conversation or 'document_versions' not in conversation or not conversation['document_versions']:
            return Response({'error': 'No document versions found for this conversation.'}, status=status.HTTP_404_NOT_FOUND)
        
        version = next((v for v in conversation['document_versions'] if v['version_number'] == version_number), None)
        if version:
            return Response({'content': version['content']}, status=status.HTTP_200_OK)
        return Response({'error': 'Version content not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error in get_version_content: {e}")
        return Response({'error': f'Error retrieving version content: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)