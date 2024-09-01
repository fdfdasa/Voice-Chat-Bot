# semantic/route.py

from flask import Blueprint, request, jsonify
from .semantic import classify_message, compare_vectors

semantic_bp = Blueprint('semantic', __name__)

@semantic_bp.route('/classify', methods=['POST'])
def classify():
    data = request.json
    message = data.get("message", "")
    category = classify_message(message)
    return jsonify({"category": category})

@semantic_bp.route('/compare_vectors', methods=['POST'])
def compare():
    data = request.json
    message = data.get("message", "")
    sample_list = data.get("samples", [])
    similarities = compare_vectors(message, sample_list)
    return jsonify({"similarities": similarities})
