from flask import Flask, request, jsonify
import db as database
db = database.connect_db()
import pymysql
from controllers.functions import get_article_recommendations, cosine_sim_overviews,cosine_sim_titles

def get_articles():
    data = request.get_json()
    dates = data.get('dates',[])
    journal = data.get('journal',[])
    input = data.get('input','')
    issue = data.get('issue')
    if db is not None:
        try:
            db.ping(reconnect=True)
            with db.cursor() as cursor:
                sort_param = request.args.get('sort', default=None)
                if sort_param == 'title':
                    sort = "ORDER BY article.title ASC"
                elif sort_param == 'publication-date':
                    sort = "ORDER BY article.publication_date DESC"
                # elif sort_param == 'recently-added':
                #     sort = "ORDER BY article.date_added DESC"
                elif sort_param == 'popular':
                    sort = "ORDER BY total_interactions DESC"
                elif sort_param == 'downloads':
                    sort = "ORDER BY total_downloads DESC"
                elif sort_param == 'views':
                    sort = "ORDER BY total_reads DESC"
                elif sort_param == 'citations':
                    sort = "ORDER BY total_citations DESC"
                        
                else:
                    sort = ""
                input_array = [i.lower().strip() for i in input.split(",")]
                if not dates or dates == []:
                    date_conditions = '1=1'  
                else:
                    date_conditions = ' OR '.join(['article.publication_date LIKE %s' for _ in dates])
                
                if not journal or journal == []:
                    journal_conditions = '1=1'  
                else:
                    journal_conditions = ' OR '.join(['article.journal_id LIKE %s' for _ in journal])
                    
                if not issue:
                    issue_conditions = '1=1'  
                else:
                    issue_conditions = f'article.issues_id =  {issue}' 
    
                title_conditions = ' OR '.join('article.title LIKE %s' for i in input_array)
                keyword_conditions = ' OR '.join('article.keyword LIKE %s' for i in input_array)
                author_condition = ' OR '.join("c.contributors LIKE %s" for i in input_array)
                id_condition = ' OR '.join('article.article_id LIKE %s' for i in input_array)
                
                query = f'''
                    SELECT 
                        article.article_id,
                        article.journal_id,
                        article.title,
                        article.author,
                        LEFT(article.abstract, 150) AS abstract,
                        article.keyword,
                        article.publication_date,
                        article.status,
                        article.issues_id,
                        issues.title,
                        journal.journal,
                        COALESCE(total_reads, 0) AS total_reads,
                        COALESCE(total_citations, 0) AS total_citations,
                        COALESCE(total_downloads, 0) AS total_downloads,
                        COALESCE(total_interactions, 0) AS total_interactions,
                        c.contributors
                    FROM 
                    article 
                    LEFT JOIN 
                        journal ON article.journal_id = journal.journal_id 
                    LEFT JOIN 
                        issues ON article.issues_id = issues.issues_id 
                    LEFT JOIN
                        (
                            SELECT
                                article_id,
                                COUNT(CASE WHEN logs.type = 'read' THEN 1 END) AS total_reads,
                                COUNT(CASE WHEN logs.type = 'citation' THEN 1 END) AS total_citations,
                                COUNT(CASE WHEN logs.type = 'download' THEN 1 END) AS total_downloads,
                                COUNT(logs.article_id) AS total_interactions
                            FROM
                                logs
                            GROUP BY
                                article_id
                        ) AS log_counts ON article.article_id = log_counts.article_id
                    LEFT JOIN(
                        SELECT article_id,
                            GROUP_CONCAT(
                                DISTINCT CONCAT(firstname, ' ', lastname, '->', orcid)  ORDER BY contributors_id SEPARATOR ', '
                            ) AS contributors
                        FROM
                            contributors
                        GROUP BY
                            article_id
                    ) AS c ON article.article_id = c.article_id
              
                    WHERE   
                    ({date_conditions})
                    AND ({journal_conditions})
                    AND ({issue_conditions})
                    AND article.status = 1 
                    AND
                    (
                        {title_conditions}
                        OR {keyword_conditions}
                        OR {author_condition}
                        OR {id_condition}
                       
                    )
                    
                    GROUP BY
                    article.article_id 
                    {sort}
                    ;
                '''
    
                input_params = [f"%{input}%" for input in input_array]
                params = [f"%{date}%" for date in dates] + [f"%{j}%" for j in journal]  +input_params + input_params + input_params + input_params
           
                # print(params)
                # print(f"{query}","para", params,"ff")
                cursor.execute(f"{query}", params)
                result = cursor.fetchall()
                db.close()
                if input.strip() != "":
                    if len(result)==0:
                        return jsonify({"message": f"No results found for {input} . Try to use comma to separate keywords"})
                    for i in range(len(result)): ## Adding contains to each result
                        result[i]["article_contains"]=[]
                    
                    article_info = [result[info]["title"]+result[info]["keyword"] for info in range(len(result))]
                    
                    for input in input_array:
                        for n,info in enumerate(article_info):
                            if input in info.lower():
                                result[n]["article_contains"].append(input)
                    result = sorted(result,  key=lambda x: len(x["article_contains"]), reverse= True)
                return jsonify({"results": result, "total": len(result)})
        except Exception as e:
            print(e)
            return jsonify({'error': 'An error occurred while fetching article data.'}), 500
    else:
        return jsonify({'message': 'Database connection error'}),500
        
def get_filters():
    if db is not None:
        db.ping(reconnect=True)
        cursor = db.cursor()
        filtersSQL ='''
                    SELECT
                        GROUP_CONCAT(DISTINCT YEAR(publication_date) ORDER BY YEAR(publication_date) DESC) AS distinct_years,
                        GROUP_CONCAT(DISTINCT CONCAT(journal.journal_id, ' -> ', journal.journal)) AS journals
                    FROM article
                    LEFT JOIN journal ON article.journal_id = journal.journal_id;
                    '''
                
        cursor.execute(filtersSQL)
        filters = cursor.fetchone()
        cursor.close()  
        db.close() 
        return jsonify(filters),200
    else:
        return jsonify({'message': 'Database connection error'}),500
        
def get_read_article():
    data = request.get_json()
    article_id = data['article_id']
    preview = data.get('preview', False)
    author_id = data.get('author_id', 0)
     
    if not article_id:
        return jsonify({'message': 'Article_id must be provided.'}), 400
    if  preview == True:
        preview_condition = 'AND 1=1'  
    else:
        preview_condition = 'AND article.status = 1'  
    if db is not None:
        try:
            db.ping(reconnect=True)
            cursor = db.cursor()
            cursor.execute(f"""
                SELECT
                    article.*,
                    journal.journal,
                    article.keyword,
                    issues.title AS issue_title,
                    issues.issn,
                    issues.number,
                    issues.volume AS issue_volume,
                    file_name.file_name,
                    COALESCE(total_reads, 0) AS total_reads,
                    COALESCE(total_citations, 0) AS total_citations,
                    COALESCE(total_downloads, 0) AS total_downloads,
                    COALESCE(total_support, 0) AS total_support,
                     COALESCE(isSupported, 0) AS isSupported,
                    COALESCE(total_interactions, 0) AS total_interactions,
                    c.contributors, c.contributors_A, c.contributors_B
                FROM
                    article
                LEFT JOIN journal ON article.journal_id = journal.journal_id
                LEFT JOIN issues ON article.issues_id = issues.issues_id 
                LEFT JOIN
                    (
                        SELECT
                            article_id,
                            COUNT(CASE WHEN logs.type = 'read' THEN 1 END) AS total_reads,
                            COUNT(CASE WHEN logs.type = 'citation' THEN 1 END) AS total_citations,
                            COUNT(CASE WHEN logs.type = 'download' THEN 1 END) AS total_downloads,
                            COUNT(CASE WHEN logs.type = 'support' THEN 1 END) AS total_support,
                            COUNT(CASE WHEN logs.type = 'support' AND logs.author_id = %s THEN 1 END) AS isSupported,
                            COUNT(logs.article_id) AS total_interactions
                        FROM
                            logs
                        GROUP BY
                            article_id
                    ) AS log_counts ON article.article_id = log_counts.article_id
                LEFT JOIN 
                    (
                        SELECT article_id,file_name
                        FROM article_final_files
                        WHERE production = 1 AND file_type = "Final"
                    ) AS file_name ON article.article_id = file_name.article_id
                LEFT JOIN(
                    SELECT article_id,
                        GROUP_CONCAT(
                            DISTINCT CONCAT(firstname, ' ', lastname, '->', orcid, '->', contributor_type, '->', email) ORDER BY contributors_id SEPARATOR ' ; '
                        ) AS contributors,
                        GROUP_CONCAT(
                            DISTINCT CONCAT(lastname, ', ', firstname) ORDER BY contributors_id SEPARATOR ' ; '
                        ) AS contributors_A,
                        GROUP_CONCAT(
                            DISTINCT CONCAT(lastname, ', ', SUBSTRING(firstname, 1, 1), '.')  ORDER BY contributors_id SEPARATOR ' ; '
                        ) AS contributors_B
                        
                    FROM
                        contributors
                    GROUP BY
                        article_id
                ) AS c
                ON
                    article.article_id = c.article_id
                WHERE
                    article.article_id = %s
                    {preview_condition}
                GROUP BY
                    journal.journal_id,
                    journal.journal,
                    article.article_id;
            """, (author_id,article_id))
           
     
            data = cursor.fetchall()
            
            if preview == False and len(data) != 0:
                cursor.execute('INSERT INTO logs (article_id, author_id) VALUES (%s, %s)', (article_id, author_id))
                db.commit()
                message =f"{article_id}  successfully inserted to read logs of user {author_id}"
            elif preview == True:
                 message = f"This is just a preview of article {article_id}"
            else:
                message =f"{article_id} failed to be inserted on read logs of user {author_id}"
                return jsonify({'message': 'Error inserting read history.'}), 400
        except pymysql.Error as e:
            return jsonify({'message': 'Error inserting read history.', 'error_details': str(e)}), 500
        finally:
            cursor.close()  
            db.close() 
    else:
        return jsonify({'message': 'Database connection error'}), 500
        
    recommendations = get_article_recommendations(article_id, cosine_sim_overviews, cosine_sim_titles)

    if isinstance(recommendations, list):  # Check if recommendations is a list
        return jsonify({
            'message': message,
            'recommendations': recommendations[1:],
            'selected_article': data
        })
    
    else:
        return jsonify({'error': recommendations})
        
def insert_support_log():
    data = request.get_json()
    article_id = data['article_id']
    author_id = data.get('author_id', '')
    
    if db is not None:
        db.ping(reconnect=True)
        with db.cursor() as cursor:
            cursor.execute("SELECT * FROM logs WHERE article_id = %s AND author_id = %s AND type='support'" , (article_id, author_id))
            support = cursor.fetchone()
            if support is None:
                cursor.execute("INSERT INTO logs (article_id, author_id, type) VALUES (%s, %s,'support')", (article_id, author_id))
                db.commit()
                return jsonify({'message': f"{article_id} successfully inserted to support log for {author_id} ",'status':True})
            else:
                cursor.execute("DELETE FROM logs WHERE article_id = %s AND author_id = %s AND type='support'", (article_id, author_id))
                db.commit()
                return jsonify({'message': f"{article_id} successfully deleted from support log for {author_id}",'status': False})
    else:
        return jsonify({'message': 'Database Connection Error'}),500
        
def insert_log():
    data = request.get_json()
    type = data.get('type','others')
    article_id = data['article_id']
    author_id = data.get('author_id', '')
    if db is not None:
        db.ping(reconnect=True)
        with db.cursor() as cursor:
            cursor.execute("INSERT INTO logs (article_id, author_id, type) VALUES (%s, %s, %s)", (article_id, author_id, type))
            db.commit()
                
        return jsonify({'message':f"{article_id} successfully inserted to {type} log for {author_id} "})
    else:
        return jsonify({'message': 'Database connection error'}),500
