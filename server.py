from flask import Flask, request, jsonify
from flask_cors import CORS
from semantic.router import create_app
from semantic.semantic import classify_message
from rag.rag import custom_qa_chain
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from datetime import datetime

app = create_app()
CORS(app)

# MongoDB connection setup
MONGO_URI = "mongodb+srv://fdfdasa:Tungquan0611@learnpage.kppavu7.mongodb.net/?retryWrites=true&w=majority&appName=LearnPage"
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client['Test']  # Replace 'Test' with your database name
collection = db['User']  # Replace 'User' with your collection name
counter_collection = db['counters']  # Collection to store counters

def get_next_sequence_value(sequence_name):
    # Increment the sequence and return the new value
    counter = counter_collection.find_one_and_update(
        {'_id': sequence_name},
        {'$inc': {'sequence_value': 1}},
        return_document=True,
        upsert=True
    )
    return counter['sequence_value']

@app.route('/process-text', methods=['POST'])
def process_text():
    data = request.get_json()
    text = data.get('text', '')

    category = classify_message(text)
    response_d = custom_qa_chain(text, category)
    
    response = {
        'response': response_d
    }
    
    return jsonify(response)

@app.route('/save-data', methods=['POST'])
def save_data():
    data = request.get_json()
    text = data.get('text', '')
    response = data.get('response', '')
    
    # Get the next sequence value for the ID
    new_id = get_next_sequence_value('user_id')
    
    # Prepare data to be saved
    save_data = {
        '_id': new_id,  # Use the new ID
        'text': text,
        'response': response,
        'timestamp': datetime.now().isoformat()
    }

    # Save the data to MongoDB
    collection.insert_one(save_data)

    # Return the saved data
    return jsonify(save_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
