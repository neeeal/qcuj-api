from flask import Flask, request, jsonify,Blueprint
import db as database
db = database.connect_db()
import json
universities_bp = Blueprint('universities',__name__)

# Load the JSON data from your file
with open('./ipynb/universities.json', 'r') as file:
    universities_data = json.load(file)
    
@universities_bp.route('/', methods=['GET'])
def search_universities():
    title = request.args.get('title', "") 
    
    universities = [uni for uni in universities_data if title.lower() in uni.lower()]
    
    results = universities
    
    return jsonify(results), 200