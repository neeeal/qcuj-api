from flask import Flask, request, jsonify,Blueprint
import db as database
db = database.connect_db()

faqs_bp = Blueprint('faqs',__name__)

@faqs_bp.route('/', methods=['GET'])
def get_faqs():
    category = request.args.get('category',"GENERAL QUESTIONS")
    limit = request.args.get('limit')
    
    
    try:
        db.ping(reconnect=True)
        with db.cursor() as cursor:
            if limit is None:
                cursor.execute('SELECT * FROM faqs')
               
            else:
                cursor.execute('SELECT * FROM faqs where category = %s LIMIT %s',(category, int(limit)))
            return jsonify({"faqs": cursor.fetchall()})
  
    except Exception as e:
        return jsonify({"error": str(e)})