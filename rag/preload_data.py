import os
import pickle
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

GOOGLE_API_KEY = 'AIzaSyBgu-HAzOWXB4uKyy_DNrslotAWlkXdhu4'

PROCESSED_FILES = {
    "physics":  "voice-main\\rag\\physics_k.pkl",
    "chitchat": "voice-main\\rag\\chitchat.pkl"
}

PRELOADED_DATA = {}

def load_processed_data(filename):

    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, 'rb') as file:
            return pickle.load(file)
    else:
        return None

def preload_data():
    global PRELOADED_DATA
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    
    for subject, filename in PROCESSED_FILES.items():
        processed_data = load_processed_data(filename)
        if processed_data:
            texts, embedded_texts = processed_data
            vector_store = Chroma.from_texts(texts, embeddings)
            PRELOADED_DATA[subject] = vector_store
        else:
            print(f"Warning: Processed data for {subject} could not be loaded from {filename}.")

preload_data()

def get_preloaded_data(subject):
    return PRELOADED_DATA.get(subject, None)

if __name__ == "__main__":
    # Preload data when this script is run
    preload_data()
    print("Data preloaded successfully.")
