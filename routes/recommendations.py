from flask import Flask, Blueprint

from controllers.recommendations_controller import get_reco_based_on_popularity, get_reco_based_on_history

recommendations_bp = Blueprint('recommendations',__name__)
@recommendations_bp.route('/', methods=['POST'])
def get_reco_based_on_popularity_route():
   return get_reco_based_on_popularity()

@recommendations_bp.route('/<int:author_id>', methods=['GET'])
def get_reco_based_on_history_route(author_id):
   return get_reco_based_on_history(author_id)