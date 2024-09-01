import difflib
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import numpy as np

def classify_message(message):
    
    
    from .samples import helpsample, chitchatSample    # Tính điểm tương đồng
    def get_similarity_ratio(message, sample_list):
        return max([difflib.SequenceMatcher(None, message, sample).ratio() for sample in sample_list])

    # Lấy tỷ lệ tương đồng cao nhất cho từng loại
    chitchat_ratio = get_similarity_ratio(message, chitchatSample)
    help_ratio = get_similarity_ratio(message, helpsample)
    # Tìm loại có tỷ lệ tương đồng cao nhất
    max_ratio = max( help_ratio, chitchat_ratio)
    
    if max_ratio == help_ratio:
        return "chitchat"
    else:
        return "chitchat"

def embed_text(text):
    """Chuyển đổi văn bản thành vector sử dụng GoogleGenerativeAIEmbeddings."""
    GOOGLE_API_KEY = 'YOUR_GOOGLE_API_KEY'  # Thay thế bằng khóa API thực tế của bạn
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=GOOGLE_API_KEY)
    return embeddings.embed_query(text)

def compare_vectors(user_text, sample_list):
    """So sánh vector của văn bản người dùng và các mẫu."""
    user_vector = embed_text(user_text)
    sample_vectors = [embed_text(sample) for sample in sample_list]
    
    # Tính toán cosine similarity
    def cosine_similarity(vec1, vec2):
        return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
    
    similarities = [cosine_similarity(user_vector, sample_vector) for sample_vector in sample_vectors]
    return similarities
