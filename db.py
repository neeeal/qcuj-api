import os
from flask import Flask
import pymysql
from dotenv import load_dotenv

load_dotenv()

_db = None
def connect_db():
    global _db
    if not _db or _db.ping() == False:
        _db = pymysql.connect(
            host=os.getenv('DATABASE_HOST'),
            user=os.getenv('DATABASE_USER'),
            password=os.getenv('DATABASE_PASSWORD'),
            db=os.getenv('DATABASE_DB'),
            connect_timeout=10,
            cursorclass=pymysql.cursors.DictCursor
        )
    return _db
        
__all__ = ['connect_db']

