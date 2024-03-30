from flask import Flask ,Blueprint
from controllers.faqs_controller import get_faqs

faqs_bp = Blueprint('faqs',__name__)

@faqs_bp.route('/', methods=['GET'])
def get_faqs_route():
    return get_faqs()