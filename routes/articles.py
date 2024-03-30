from flask import Flask, Blueprint
from controllers.articles_controller import get_articles, get_filters, get_read_article, insert_support_log, insert_log

articles_bp = Blueprint('articles',__name__)

@articles_bp.route('/', methods=['POST'])
def get_articles_route():
    return get_articles()
    
@articles_bp.route('/filters', methods=['GET'])
def get_filters_route():
    return get_filters()
    
@articles_bp.route('/logs/read', methods=['POST'])
def get_read_article_route():
    return get_read_article()
    
@articles_bp.route('/logs',methods=['POST'])
def insert_log_route():
    return insert_log()

@articles_bp.route('/logs/support', methods=['POST'])
def insert_support_log_route():
    return insert_support_log()

