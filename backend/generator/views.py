from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from django.conf import settings
import google.generativeai as genai
import json
from django.http import FileResponse
import markdown
from xhtml2pdf import pisa
from io import BytesIO
from .mongo_client import get_all_conversations, get_conversation_by_id, save_conversation, update_conversation, delete_conversation
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.utils.crypto import get_random_string
import os
import cloudinary.uploader

from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def chat(request):
    from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate, AIMessagePromptTemplate
    """
    API endpoint for the conversational legal document generator.
    """
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY == '':
        return Response({'error': 'GEMINI_API_KEY is not configured in your .env file or is empty.'}, status=500)

    messages = request.data.get('messages', [])
    if not messages:
        return Response({'error': 'Messages are required'}, status=400)

    try:
        signature_file = request.FILES.get('signature')
        if signature_file:
            try:
                upload_result = cloudinary.uploader.upload(signature_file)
                signature_url = upload_result['secure_url']
                # Append a system message to the user's message
                messages[-1]['text'] += f"\n\n(System: The user has uploaded a signature. Please place it in the appropriate section of the document using the following markdown: ![Signature]({signature_url}))"
            except Exception as e:
                return Response({'error': f'Error uploading signature: {e}'}, status=500)

        genai.configure(api_key=settings.GEMINI_API_KEY)

        system_instruction_text = """You are a helpful legal assistant. Your goal is to help the user create a legal document.
- First, ask follow-up questions to gather all the necessary details.
- When you have enough information, generate the full legal document.
- The document **must** be in well-structured **Markdown format**. Use headings (`#`, `##`), lists (`*`, `-`), bold (`**text**`), and italics (`*text`*) to create a professional and readable document.
- When you are ready to generate the document, provide it in a JSON format like this: ```json{"type": "document", "text": "...your Markdown document here..."}```.
- If the user asks to update some information, you must look for the previous document you generated in the conversation history. You will use that document as the basis for your new version.
- You must then regenerate the **entire** document, incorporating the user's requested changes, and provide it again in the same JSON format. Do not just provide the updated line or a confirmation message.
- **Signature Handling:** If the user uploads a signature, you will see a system message like `(System: The user has uploaded a signature...)` with a URL. When you generate the document, you **must** include this signature at the appropriate signature lines using the provided URL in the correct markdown format: `![Signature](URL)`. **Do NOT acknowledge the system message about the signature upload in your conversational response.**
"""

        model = genai.GenerativeModel(
            'models/gemini-2.5-flash-lite',
            system_instruction=system_instruction_text
        )

        # Separate history from the current message
        history = messages[:-1]
        current_message = messages[-1]['text']

        gemini_history = []
        for message in history:
            role = 'user' if message['sender'] == 'user' else 'model'
            gemini_history.append({'role': role, 'parts': [message['text']]})

        chat_session = model.start_chat(history=gemini_history)
        response = chat_session.send_message(current_message)

        print(f"Raw model response object: {response}")
        print(f"Model response text: {response.text}")

        # The response from the model is just text, so we need to parse it to see
        # if it is a question or the final document.
        # For now, we will assume that if the response contains "```json", it is the final document in JSON format.
        # Otherwise, it is a question.
        if '```json' in response.text:
            # It's the final document
            # Extract the JSON part from the response
            json_str = response.text.split('```json')[1].split('```')[0]
            document_data = json.loads(json_str)
            return Response(document_data)
        else:
            # It's a question
            return Response({'type': 'question', 'text': response.text})

    except Exception as e:
        print(f"Error in chat view: {e}")
        print(f"Type of error: {type(e)}")
        return Response({'error': str(e)}, status=500)

@api_view(['POST'])
def download_pdf(request):
    """
    API endpoint to download a legal document as PDF.
    """
    document_content = request.data.get('document_content')
    if not document_content:
        return Response({'error': 'Document content is required'}, status=400)

    try:
        pdf_file = _generate_pdf_from_markdown(document_content)
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="legal_document.pdf"'
        return response
    except Exception as e:
        return Response({'error': f'Error generating PDF: {e}'}, status=500)

def _generate_pdf_from_markdown(markdown_content):
    """Helper function to convert markdown string to a PDF file response."""
    html_content = markdown.markdown(markdown_content)

    pdf_style_css = """
        @page {
            size: a4 portrait;
            margin: 1.2cm;
        }
        body {
            font-family: "Times New Roman", Times, serif;
            font-size: 11pt;
            line-height: 1.3;
            color: #000000;
        }
        h1, h2, h3, h4, h5, h6 {
            font-family: "Times New Roman", Times, serif;
            font-weight: bold;
            color: #000000;
            margin-top: 1.2em;
            margin-bottom: 0.6em;
            line-height: 1.15;
        }
        h1 {
            font-size: 16pt;
            text-align: center;
            text-transform: uppercase;
            margin-bottom: 1.5em;
        }
        h2 {
            font-size: 14pt;
            text-transform: uppercase;
            border-bottom: 1px solid #000000;
            padding-bottom: 0.2em;
        }
        h3 {
            font-size: 12pt;
            font-weight: bold;
            text-decoration: underline;
        }
        p {
            margin-bottom: 0.8em;
            text-align: justify;
            text-indent: 1.25cm; /* Indent first line of paragraphs */
        }
        /* Don't indent first paragraph after a heading */
        h1 + p, h2 + p, h3 + p, h4 + p, h5 + p, h6 + p {
            text-indent: 0;
        }
        ul, ol {
            margin-bottom: 0.8em;
            padding-left: 1.5cm;
        }
        li {
            margin-bottom: 0.3em;
            text-align: justify;
        }
        strong, b {
            font-weight: bold;
        }
        em, i {
            font-style: italic;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 1em;
            border: 1px solid #333333;
        }
        th, td {
            border: 1px solid #333333;
            padding: 6px;
            text-align: left;
            vertical-align: top;
        }
        th {
            background-color: #e0e0e0;
            font-weight: bold;
        }
        hr {
            width: 250px;
            margin-left: 0;
            border: 0.5px solid #000;
        }
        /* Signature sizing and spacing */
        img[alt~="signature"][alt~="landlord"] {
            display: block;
            width: 180px;
            height: 80px;
            object-fit: contain;
            margin-top: 8mm;   /* place below landlord text */
            margin-bottom: 0;
        }
        img[alt~="signature"][alt~="tenant"] {
            display: block;
            width: 180px;
            height: 80px;
            object-fit: contain;
            margin-top: 0;
            margin-bottom: 8mm; /* place above tenant text */
        }
        /* Remove header and footer for a more traditional look */
    """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Legal Document</title>
        <meta charset=\"utf-8\">
        <style>{pdf_style_css}</style>
    </head>
    <body>{html_content}</body>
    </html>
    """

    result_file = BytesIO()
    pisa_status = pisa.CreatePDF(full_html, dest=result_file)

    if pisa_status.err:
        raise Exception(f'PDF generation error: {pisa_status.err}')

    result_file.seek(0)
    return result_file

@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def upload_signature(request):
    """Accepts an image upload and returns its accessible URL for embedding in markdown."""
    file_obj = request.FILES.get('signature') or request.FILES.get('file')
    if not file_obj:
        return Response({'error': 'No file uploaded. Use form field name "signature".'}, status=400)

    try:
        upload_result = cloudinary.uploader.upload(file_obj)
        return Response({'url': upload_result['secure_url']}, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=500)

@api_view(['GET'])
def download_conversation_pdf(request, pk):
    """
    Downloads the latest document from a conversation as a PDF.
    """
    conversation = get_conversation_by_id(pk)
    if not conversation or not conversation.get('latest_document'):
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)

    try:
        document_content = conversation['latest_document']
        pdf_file = _generate_pdf_from_markdown(document_content)
        
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{conversation.get("title", "legal_document")}.pdf"'
        return response
    except Exception as e:
        return Response({'error': f'Error generating PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        latest_document = request.data.get('latest_document') # Get the new field
        if not title or not messages:
            return Response({'error': 'Title and messages are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        conversation_id = save_conversation(title, messages, latest_document)
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
        latest_document = request.data.get('latest_document')
        if not title or not messages:
            return Response({'error': 'Title and messages are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        success = update_conversation(pk, title, messages, latest_document)
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