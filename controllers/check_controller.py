from flask import Flask, request, jsonify
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.models import load_model
from controllers.functions import  get_originality_score,load_tokenizer,load_label_encoder,preprocess_abstract,classify, get_reviewer_recommendation
import db as database
db = database.connect_db()

def check_originality():
    if db is not None:
        try:
            data = request.get_json()
            title = data['title']
            abstract = data['abstract']
            
            similar_articles = get_originality_score(title, abstract)
        
            if isinstance(similar_articles, list): 
                if len(similar_articles) > 0:
                    return jsonify({
                        'flagged': True,
                        'highest_simlarity':similar_articles[0]['score']['total'],
                        'similar_articles': similar_articles
                    })  
                return jsonify({
                        'flagged': False,
                        'similar_articles': similar_articles
                    })  
            return jsonify({'error':'error'}),400
        except Exception as e:
            return jsonify({'message': str(e)}),500
    else:
        return jsonify({'message': 'Database connection error'}),500
        
def check_originality_by_id():
    data = request.get_json()
    id = data.get('id')
    if id is None:
        return jsonify({'error': 'No ID provided'})
    if db is not None:
        try:
            db.ping(reconnect=True)
            cursor = db.cursor()
            cursor.execute("""
                SELECT article.article_id, article.title, article.abstract, article.publication_date,article.status, c.contributors 
                FROM article 
                LEFT JOIN(
                    SELECT 
                    	article_id, GROUP_CONCAT(DISTINCT CONCAT(firstname,' ',lastname,'->',orcid) SEPARATOR ', ') AS contributors
     				FROM contributors GROUP BY article_id) AS c ON article.article_id = c.article_id
                WHERE article.article_id = %s
                GROUP BY article.article_id
            """, (id,))
            
            article_data = cursor.fetchone()
            cursor.close()  
            db.close() 
    
            # print(article_data,"arttt",id)
            if article_data:
                title = article_data['title']
                abstract = article_data['abstract']
                similar_articles = get_originality_score(title, abstract,False)
                
                similar_articles = [article for article in similar_articles if article['article_id'] != id]
                
                if isinstance(similar_articles, list) and similar_articles:
                    return jsonify({
                        'flagged': True,
                        'similar_articles': similar_articles,
                        'selected_article': article_data
                    })
                else:
                    return jsonify({'flagged': False, 'similar_articles': []})
            else:
                return jsonify({'error': 'Article not found'})
        except Exception as e:
            return jsonify({'message': str(e)}),500
    else:
        return jsonify({'message': 'Database connection error'}),500

model = load_model('models//finalClassifier_v0015//model.h5')

def classify_article():
    data = request.get_json()
    abstract = data['abstract']
    title = data['title']
    if db is not None:   
        try:
            ## Load tokenizer and encoder
            tokenizer = load_tokenizer('models//finalClassifier_v0015//tokenizer.pickle')
            # label_encoder = load_label_encoder('models//classifier_v07//label_encoder.pickle')
            input = title + " " + abstract
            ## Preprocess abstract
            
            input_data, input_label = preprocess_abstract(input,tokenizer)
            if input_data is None:
                return jsonify({'message': 'No suggested journal matches your article. Please review your article details or select from the provided choices.'}), 400
            else:
                ## classify abstract
                result = classify(input_data, model)
                
                return {'journal_classification': f"{result+1}"}
        except Exception as e:
            return jsonify({'message': str(e)}),500
    else:
        return jsonify({'message': 'Database connection error'}),500
def recommend_reviewers():
    data = request.get_json()
    id = data['id']
    category = data.get('category', 'score') 
    # abstract = data['abstract']
    
    if id is None:
        return jsonify({'error': 'No ID provided'})
    
    if db is not None:   
        try:
            db.ping(reconnect=True)
            cursor = db.cursor()
            cursor.execute("""
                SELECT article.article_id, article.title, article.keyword, article.publication_date
                FROM article 
                WHERE article.article_id = %s
            """, (id,))
            
            article_data = cursor.fetchone()
            cursor.close()  
            db.close() 
    
            if article_data:
                title = article_data['title']
                keywords = article_data['keyword']
                input = title + ' ' + keywords
                recommended_reviewers = get_reviewer_recommendation(input,category)
                return jsonify({
                    "sorted_reviewers": recommended_reviewers,
                    "article_title": title 
                }), 200
            return jsonify({'error': 'Article not found'}),400
                
        except Exception as e:
            return jsonify({'message': str(e)}),500
    else:  
        return jsonify({'message': 'Database connection error'}),500