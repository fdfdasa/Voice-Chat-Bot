import os
import json
from datetime import datetime
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
import warnings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains import RetrievalQA
from langchain_core.prompts import PromptTemplate
from rag.preload_data import get_preloaded_data
import re
import spacy
from spacy.training import Example
from spacy.language import Language
from transformers import AutoModel, AutoTokenizer
import torch
from rag.test_data import test_data
from rag.api import template
from rag.api import template2
from rag.api import groq_api_key
from rag.api import GOOGLE_API_KEY
# Import đối tượng user_info từ server.py
from groq import Groq

warnings.filterwarnings("ignore")

SAVE_DIRECTORY = 'saved_responses'

# Ensure the directory exists
if not os.path.exists(SAVE_DIRECTORY):
    os.makedirs(SAVE_DIRECTORY)

# Configure the generative AI with the API key
genai.configure(api_key=GOOGLE_API_KEY)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=GOOGLE_API_KEY)

QA_CHAIN_PROMPT = PromptTemplate.from_template(template)

previous_message = None
state = False  # Initialize state to False

def setup_qa_chain(category, user_id, user_name):
    # Tạo đường dẫn file .pkl dựa trên thông tin người dùng
    filename = f"physics_k.pkl"
    file_path = os.path.join("rag", filename)
    print(file_path)
    # Kiểm tra nếu file tồn tại, nạp vector_store từ file này
    if os.path.exists(file_path):
        vector_store = get_preloaded_data(category)
    else:
        vector_store = None

    if not vector_store:
        return None

    vector_index = vector_store.as_retriever(search_kwargs={"k": 5})
    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=GOOGLE_API_KEY, temperature=0.65, convert_system_message_to_human=True)
    qa_chain = RetrievalQA.from_chain_type(
        model,
        retriever=vector_index,
        return_source_documents=True
    )
    return qa_chain

def setup_qa_chain_chitchat():
    # Tạo đường dẫn file .pkl dựa trên thông tin người dùng
    filename = f"chitchat.pkl"
    file_path = os.path.join("rag", filename)

    # Kiểm tra nếu file tồn tại, nạp vector_store từ file này
    if os.path.exists(file_path):
        vector_store = get_preloaded_data(file_path)
    else:
        vector_store = None

    if not vector_store:
        return None

    vector_index = vector_store.as_retriever(search_kwargs={"k": 5})
    model = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=GOOGLE_API_KEY, temperature=0.65, convert_system_message_to_human=True)
    qa_chain = RetrievalQA.from_chain_type(
        model,
        retriever=vector_index,
        return_source_documents=True
    )
    return qa_chain

def custom_qa_chain(query, category):

    
    # Khởi tạo hoặc cập nhật danh sách tin nhắn gần đây
    if not hasattr(custom_qa_chain, 'recent_messages'):
        custom_qa_chain.recent_messages = []
    
    # Thêm tin nhắn mới vào danh sách
    custom_qa_chain.recent_messages.append({"role": "user", "content": query})
    
    # Giữ tối đa 5 tin nhắn gần nhất
    custom_qa_chain.recent_messages = custom_qa_chain.recent_messages[-5:]
    
    # Tạo chuỗi tin nhắn để cung cấp ngữ cảnh
    context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in custom_qa_chain.recent_messages])

    if category == 'chitchat':
        # Thiết lập chuỗi QA cho chitchat
        qa_chain = setup_qa_chain_chitchat()
        if not qa_chain:
            # Nếu không có dữ liệu từ file .pkl, sử dụng mô hình "Llama 3.1 70B" qua Groq để xử lý chitchat
            client = Groq(api_key=groq_api_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"Đây là ngữ cảnh cuộc trò chuyện gần đây trừ khi người dùng yêu cầu, nếu không bạn không cần lặp lại các thông tin đã nói, và đây là ngữ cảnh:\n{context}"
                    },
                    {
                        "role": "user",
                        "content": template2 + query,
                    }
                ],
                model="llama-3.1-70b-versatile",
            )
            response = chat_completion.choices[0].message.content
            # Xử lý response để thêm thẻ <br> sau dấu ":" và trước dấu "*"
            response = response.replace("\n*", "<br>*")
            # Xử lý nội dung giữa 4 dấu *
            response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response)
            formatted_response = f"""
                {response}
            """
            print(formatted_response)
            
            # Thêm phản hồi vào danh sách tin nhắn gần đây
            custom_qa_chain.recent_messages.append({"role": "assistant", "content": response})
            custom_qa_chain.recent_messages = custom_qa_chain.recent_messages[-5:]
            
            return formatted_response
        else:
            # Nếu có dữ liệu từ file .pkl, thực hiện truy vấn thông qua chuỗi QA
            result = qa_chain({"query": query})

            # Kết hợp kết quả từ file .pkl với mô hình
            enriched_query = f"Using this context: {context}\nAnd this information: {result['result']}. Please answer the question: {query}"
            client = Groq(api_key=groq_api_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": f"Đây là ngữ cảnh cuộc trò chuyện gần đây, trừ khi người dùng yêu cầu, nếu không bạn không cần lặp lại các thông tin đã nói và đây là ngữ cảnh:\n{context}"
                    },
                    {
                        "role": "user",
                        "content": template2 + enriched_query,
                    }
                ],
                model="llama-3.1-70b-versatile",
            )
            response = chat_completion.choices[0].message.content
            # Xử lý response để thêm thẻ <br> sau dấu ":" và trước dấu "*"
            response = response.replace("\n*", "<br>*")
            # Xử lý nội dung giữa 4 dấu *
            response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', response)
            formatted_response = f"""
                {response}
            """
            print(formatted_response)
            
            # Thêm phản hồi vào danh sách tin nhắn gần đây
            custom_qa_chain.recent_messages.append({"role": "assistant", "content": response})
            custom_qa_chain.recent_messages = custom_qa_chain.recent_messages[-5:]
            
            return formatted_response
        
    elif category in ['help']:  # Initialize qa_chain here
        return "Help"

    # qa_chain = setup_qa_chain(category, user_id, user_name)
    result = qa_chain({"query": query})
    return format_response(result["result"])

def format_response(response):
    # Định dạng tiêu đề chính (thời gian làm bài, các phần của đề thi)
    formatted_response = response
    print("trước khi format")
    print(response)
    # Thêm định dạng cho tiêu đề (h1, h2, h3)
    formatted_response = re.sub(r'^# (.+)$', r'<h1 style="color: #3333ff; font-size: 24px; margin-top: 20px;">\1</h1>', formatted_response, flags=re.MULTILINE)
    formatted_response = re.sub(r'^## (.+)$', r'<h2 style="color: #ff3333; font-size: 20px; margin-top: 15px;">\1</h2>', formatted_response, flags=re.MULTILINE)
    formatted_response = re.sub(r'^### (.+)$', r'<h3 style="color: #ff9900; font-size: 18px; margin-top: 10px;">\1</h3>', formatted_response, flags=re.MULTILINE)

    # Định dạng văn bản in đậm và in nghiêng
    formatted_response = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', formatted_response)
    formatted_response = re.sub(r'\*(.+?)\*', r'<em>\1</em>', formatted_response)

    # Định dạng danh sách gạch đầu dòng và đánh số
    formatted_response = re.sub(r'^\* (.+)$', r'<ul style="margin: 0; padding: 0;"><li style="margin-left: 20px;">\1</li></ul>', formatted_response, flags=re.MULTILINE)
    formatted_response = re.sub(r'^\d+\. (.+)$', r'<ol style="margin: 0; padding: 0;"><li style="margin-left: 20px;">\1</li></ol>', formatted_response, flags=re.MULTILINE)

    # Gộp các danh sách liền kề thành một khối
    formatted_response = re.sub(r'(<\/ul>\s*<ul>)', '', formatted_response, flags=re.DOTALL)
    formatted_response = re.sub(r'(<\/ol>\s*<ol>)', '', formatted_response, flags=re.DOTALL)

    # Đảm bảo xuống dòng với thẻ <br> và căn lề trái
    formatted_response = re.sub(r'([.!?])\n', r'\1<br>', formatted_response)
    formatted_response = re.sub(r'\n', r'<br>', formatted_response)  # Thêm thẻ <br> cho các xuống dòng còn lại

    # Bao quanh toàn bộ nội dung bằng thẻ <p> và chia khối cho mỗi phần
    formatted_response = re.sub(r'(\*\*I\.\*\*.*?)(?=\*\*II\.\*|\Z)', r'<div class="trac-nghiem" style="margin-bottom: 20px;">\1</div>', formatted_response, flags=re.DOTALL)
    formatted_response = re.sub(r'(\*\*II\.\*\*.*?)(?=\*\*III\.\*|\Z)', r'<div class="tu-luan" style="margin-bottom: 20px;">\1</div>', formatted_response, flags=re.DOTALL)
    formatted_response = re.sub(r'(\*\*III\.\*\*.*?)(?=\*\*IV\.\*|\Z)', r'<div class="dung-sai" style="margin-bottom: 20px;">\1</div>', formatted_response, flags=re.DOTALL)
    formatted_response = re.sub(r'(\*\*IV\.\*\*.*)', r'<div class="dien-tu" style="margin-bottom: 20px;">\1</div>', formatted_response, flags=re.DOTALL)

    # Định dạng các ký tự đặc biệt và toán học
    formatted_response = formatted_response.replace('&theta;', '&#952;')
    formatted_response = formatted_response.replace('&Sigma;', '&#931;')

    # Định dạng màu sắc cho các phần quan trọng
    formatted_response = re.sub(r'\[color=(\w+)\](.+?)\[/color\]', r'<span style="color:\1;">\2</span>', formatted_response)

    # Định dạng khối nội dung với nền và canh lề
    formatted_response = re.sub(r'\[highlight\](.+?)\[/highlight\]', r'<div style="background-color: #f0f8ff; padding: 10px; margin-bottom: 10px;">\1</div>', formatted_response)
    formatted_response = re.sub(r'\[center\](.+?)\[/center\]', r'<p style="text-align: center;">\1</p>', formatted_response)
    formatted_response = re.sub(r'\[justify\](.+?)\[/justify\]', r'<p style="text-align: justify;">\1</p>', formatted_response)

    # Tự động sửa lỗi trình bày (nếu có)
    formatted_response = formatted_response.replace('<ul></ul>', '').replace('<ol></ol>', '')
    print("sau khi format")
    print(formatted_response)
    return formatted_response


if __name__ == "__main__":
    print("Data preloaded successfully.")
