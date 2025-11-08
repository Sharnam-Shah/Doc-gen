from rest_framework.decorators import api_view, parser_classes
from rest_framework.response import Response
from django.http import FileResponse
import markdown
from xhtml2pdf import pisa
from io import BytesIO
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
import cloudinary.uploader
from documents.mongo_client import get_conversation_by_id


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
    """
    Helper function to convert markdown string to a PDF file response.
    This function is used by the download_pdf view.
    """
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
    """
    Accepts an image upload and returns its accessible URL for embedding in markdown.
    """
    file_obj = request.FILES.get('signature') or request.FILES.get('file')
    if not file_obj:
        return Response({'error': 'No file uploaded. Use form field name "signature".'}, status=400)

    try:
        upload_result = cloudinary.uploader.upload(file_obj)
        return Response({'url': upload_result['secure_url']}, status=201)
    except Exception as e:
        return Response({'error': str(e)}, status=500)


@api_view(['GET'])
def download_latest_conversation_pdf(request, pk):
    """
    Downloads the latest document content from a conversation as a PDF.
    """
    conversation = get_conversation_by_id(pk)
    if not conversation or 'document_versions' not in conversation or not conversation['document_versions']:
        return Response({'error': 'No document content found for this conversation.'}, status=status.HTTP_404_NOT_FOUND)

    try:
        # Get the content of the latest version
        latest_version_content = conversation['document_versions'][-1]['content']
        pdf_file = _generate_pdf_from_markdown(latest_version_content)
        
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{conversation.get("title", "legal_document")}.pdf"'
        return response
    except Exception as e:
        return Response({'error': f'Error generating PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def download_version_pdf(request, pk, version_number):
    """
    Downloads a specific document version from a conversation as a PDF.
    """
    try:
        conversation = get_conversation_by_id(pk)
        if not conversation or 'document_versions' not in conversation or not conversation['document_versions']:
            return Response({'error': 'No document versions found for this conversation.'}, status=status.HTTP_404_NOT_FOUND)
        
        version = next((v for v in conversation['document_versions'] if v['version_number'] == version_number), None)
        if not version:
            return Response({'error': 'Version content not found'}, status=status.HTTP_404_NOT_FOUND)

        pdf_file = _generate_pdf_from_markdown(version['content'])
        filename = f"{conversation.get("title", "legal_document")}_v{version_number}.pdf"
        
        response = FileResponse(pdf_file, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        print(f"Error in download_version_pdf: {e}")
        return Response({'error': f'Error generating PDF: {e}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)