from pymongo import MongoClient
from bson.objectid import ObjectId
from django.conf import settings
import certifi



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
    """Fetches all conversations, returning the id, title, created_at, and latest_document."""
    try:
        # Project the fields we need for the list view
        conversations = conversations_collection.find({}, {'title': 1, 'created_at': 1, 'latest_document': 1})
        # Convert ObjectId to string for JSON serialization
        return [{**conv, '_id': str(conv['_id'])} for conv in conversations]
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

def save_conversation(title, messages, latest_document=None):
    """Saves a new conversation to the database."""
    from datetime import datetime
    try:
        conversation_doc = {
            'title': title,
            'messages': messages,
            'latest_document': latest_document,
            'created_at': datetime.utcnow()
        }
        result = conversations_collection.insert_one(conversation_doc)
        return str(result.inserted_id)
    except Exception as e:
        print(f"Error saving conversation: {e}")
        return None

def update_conversation(conversation_id, title, messages, latest_document=None):
    """Updates an existing conversation."""
    from datetime import datetime
    try:
        update_doc = {
            '$set': {
                'title': title,
                'messages': messages,
                'latest_document': latest_document,
                'updated_at': datetime.utcnow()
            }
        }
        conversations_collection.update_one({'_id': ObjectId(conversation_id)}, update_doc)
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
