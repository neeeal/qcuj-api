from flask import Flask, Blueprint
from controllers.journal_controller import get_journal, get_issues, get_issue,get_articles_by_issues

journal_bp = Blueprint('journal',__name__)

@journal_bp.route('/', methods=['GET'])
def get_journal_route():
    return get_journal()
    
@journal_bp.route('/issues', methods=['GET'])
def get_issues_route():
    return get_issues()
    
@journal_bp.route(f'/issues/<int:issue_id>', methods=['GET'])
def get_issue_route(issue_id):
   return get_issue(issue_id)
        
@journal_bp.route('/issues/articles', methods=['GET'])
def get_articles_by_issues_route():
    return get_articles_by_issues()