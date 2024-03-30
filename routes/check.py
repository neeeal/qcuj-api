from flask import Flask, Blueprint

from controllers.check_controller import  check_originality,check_originality_by_id, classify_article,recommend_reviewers
import db as database
db = database.connect_db()

check_bp = Blueprint('check',__name__)
@check_bp.route('/duplication', methods=['POST'])
def check_originality_route():
    return check_originality()

@check_bp.route('/duplication/v2', methods=['POST'])
def check_originality_by_id_route():
    return check_originality_by_id()

@check_bp.route('/journal', methods=['POST'])
def classify_article_route():
    return classify_article()
@check_bp.route('/reviewers', methods=['POST'])
def recommend_reviewers_route():
    return recommend_reviewers()