from pymongo import MongoClient
from bson.objectid import ObjectId
from django.conf import settings
import certifi
from datetime import datetime


def get_db():
    mongo_uri = settings.MONGO_URI
    if not mongo_uri:
        raise Exception("MONGO_URI is not configured in your environment variables.")
    client = MongoClient(mongo_uri, tlsCAFile=certifi.where())
    db = client.get_default_database() # The database name is part of the connection string
    return db

db = get_db()
conversations_collection = db['conversations']

def get_all_conversations():
    """Fetches all conversations, returning the id, title, created_at, and the latest document content."""
    try:
        conversations = conversations_collection.find({}, {'title': 1, 'created_at': 1, 'document_versions': 1})
        # Convert ObjectId to string for JSON serialization and get latest document
        result = []
        for conv in conversations:
            conv['_id'] = str(conv['_id'])
            if 'document_versions' in conv and conv['document_versions']:
                conv['latest_document'] = conv['document_versions'][-1]['content']
            else:
                conv['latest_document'] = ''
            result.append(conv)
        return result
    except Exception as e:
        print(f"Error fetching all conversations: {e}")
        return []

def get_conversation_by_id(conversation_id):
    """Fetches a single conversation by its ID."""
    try:
        conversation = conversations_collection.find_one({'_id': ObjectId(conversation_id)})
        if conversation:
            conversation['_id'] = str(conversation['_id'])
        return conversation
    except Exception as e:
        print(f"Error fetching conversation by ID: {e}")
        return None

def save_conversation(title, messages, initial_document_content=None, uploaded_by=None, notes=None):
    """Saves a new conversation to the database, creating the first document version."""
    current_time = datetime.utcnow()
    document_versions = []
    if initial_document_content is not None:
        document_versions.append({
            'version_number': 0, # Initial version is 0
            'content': initial_document_content,
            'uploaded_at': current_time,
            'uploaded_by': uploaded_by,
            'notes': notes or 'Initial Document',
        })

    try:
        conversation_doc = {
            'title': title,
            'messages': messages,
            'document_versions': document_versions,
            'created_at': current_time,
            'updated_at': current_time,
        }
        result = conversations_collection.insert_one(conversation_doc)
        print(f"[DEBUG] New conversation saved with ID: {result.inserted_id}")
        if document_versions:
            print(f"[DEBUG] Initial version (0) content length: {len(document_versions[0]['content'])}")
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error saving conversation: {e}")
        return None

def update_conversation(conversation_id, title, messages, new_document_content=None, uploaded_by=None, notes=None):
    """Updates an existing conversation, appending a new document version."""
    current_time = datetime.utcnow()
    update_doc = {
        '$set': {
            'title': title,
            'messages': messages,
            'updated_at': current_time,
        }
    }

    existing_conv = get_conversation_by_id(conversation_id)
    print(f"[DEBUG] update_conversation called for ID: {conversation_id}")
    print(f"[DEBUG] Existing conversation found: {bool(existing_conv)}")

    if existing_conv:
        # Determine the next version number
        next_version_number = 0
        if 'document_versions' in existing_conv and existing_conv['document_versions']:
            next_version_number = max(v['version_number'] for v in existing_conv['document_versions']) + 1
        print(f"[DEBUG] Next version number: {next_version_number}")
        
        # Append the new document content as a new version
        if new_document_content is not None:
            new_version_entry = {
                'version_number': next_version_number,
                'content': new_document_content,
                'uploaded_at': current_time,
                'uploaded_by': uploaded_by,
                'notes': notes or f'Version {next_version_number} update',
            }
            update_doc['$push'] = {'document_versions': new_version_entry}
            print(f"[DEBUG] Pushing new version entry: Version {new_version_entry['version_number']}, Content length: {len(new_version_entry['content'])}")
        else:
            print("[DEBUG] new_document_content is None, not pushing new version.")

    try:
        result = conversations_collection.update_one({'_id': ObjectId(conversation_id)}, update_doc)
        print(f"[DEBUG] MongoDB update result: Matched {result.matched_count}, Modified {result.modified_count}")
        return True
    except Exception as e:
        print(f"Error updating conversation: {e}")
        return False

def delete_conversation(conversation_id):
    """Deletes a conversation from the database."""
    try:
        conversations_collection.delete_one({'_id': ObjectId(conversation_id)})
        return True
    except Exception as e:
        print(f"Error deleting conversation: {e}")
        return False

def get_document_version_content(conversation_id, version_number):
    """Retrieves the content of a specific document version from a conversation."""
    try:
        conversation = conversations_collection.find_one(
            {'_id': ObjectId(conversation_id)},
            {'document_versions': {'$elemMatch': {'version_number': version_number}}}
        )
        if conversation and 'document_versions' in conversation and conversation['document_versions']:
            return conversation['document_versions'][0]['content']
        return None
    except Exception as e:
        print(f"Error retrieving document version content: {e}")
        return None
