from flask import Flask, request, jsonify
import db as database
db = database.connect_db()
import numpy as np

def get_journal():
    param = request.args.get('id')
    if db is not None:
        try:
            db.ping(reconnect=True)
            with db.cursor() as cursor:
                if param is None:
                    cursor.execute('SELECT * FROM journal')
                    return jsonify({"journal": cursor.fetchall()})
                else:
                    cursor.execute('SELECT * FROM journal WHERE journal_id = %s', (param,))
                    return jsonify({"journalDetails": cursor.fetchone()})
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return jsonify({'message':'Database connection error'}),500
def get_issues():
    param = request.args.get('journal_id')
    if db is not None:
        try:
            db.ping(reconnect=True)
            db.ping(reconnect=True)
            with db.cursor() as cursor:
                if param is None:
                    return jsonify({"message": "journal_id parameter is required"})
                else:
                    cursor.execute('SELECT * FROM issues WHERE journal_id = %s', (param,))
                    issues = cursor.fetchall()
    
                    # Group issues by year
                    issuesPerYear = {}
                    for issue in issues:
                        publication_year = issue.get('year')
                        if publication_year:
                            if publication_year not in issuesPerYear:
                                issuesPerYear[publication_year] = []
                            issuesPerYear[publication_year].append(issue)
    
                    # jsonify the grouped issues
                    return jsonify({"issuesPerYear": issuesPerYear})
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return jsonify({"message": "Database connection error"}),500
        
def get_issue(issue_id):
    if db is not None:
        try:
            db.ping(reconnect=True)
            with db.cursor() as cursor:
                if issue_id is None:
                    return jsonify({"message": "issue_id parameter is required"})
                else:
                    cursor.execute(
                        '''
                        SELECT issues.*, journal.journal FROM issues
                        LEFT JOIN journal ON issues.journal_id = journal.journal_id
                        WHERE issues.issues_id = %s;
                        ''', (issue_id,)
                    )
                    issue = cursor.fetchone()
    
                    return jsonify( issue)
        except Exception as e:
            return jsonify({"error": str(e)})
    else:
        return jsonify({"message": "Database error"}),500
        
def get_articles_by_issues():

    issue = request.args.get('issue')
    page = request.args.get('page',1)
    offset = (int(page) -1)* 10
    if db is not None:
        try:
            db.ping(reconnect=True)
            with db.cursor() as cursor:
                if not issue:
                    issue_conditions = '1=1'  
                else:
                    issue_conditions = f'article.issues_id =  {issue}' 
                
                query = f'''
                    SELECT 
                        article.article_id,
                        LEFT(article.abstract, 180) AS abstract,
                        article.title,
                        file_name.file_name,
                        COALESCE(total_reads, 0) AS total_reads,
                        COALESCE(total_citations, 0) AS total_citations,
                        COALESCE(total_downloads, 0) AS total_downloads
                    FROM article 
                    LEFT JOIN 
                        (
                            SELECT article_id,file_name
                            FROM article_final_files
                            WHERE production = 1 AND file_type = "final"
                        ) AS file_name ON article.article_id = file_name.article_id
                    LEFT JOIN
                        (
                            SELECT
                                article_id,
                                COUNT(CASE WHEN logs.type = 'read' THEN 1 END) AS total_reads,
                                COUNT(CASE WHEN logs.type = 'citation' THEN 1 END) AS total_citations,
                                COUNT(CASE WHEN logs.type = 'download' THEN 1 END) AS total_downloads
                            FROM logs
                            GROUP BY article_id
                        ) AS log_counts ON article.article_id = log_counts.article_id
                    WHERE
                         article.status = 1
                         AND
                         {issue_conditions}
                    GROUP BY
                        article.article_id 
                    LIMIT 10
                    OFFSET {offset}
                '''
    
                cursor.execute(query)
                result = cursor.fetchall()
             
                return jsonify(result)
        except Exception as e:
            print(e)
            return jsonify({'error': 'An error occurred while fetching article data.'}), 500
    else:
        return jsonify({'message': 'Database error'}), 500