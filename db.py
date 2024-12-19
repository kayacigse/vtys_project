import mysql.connector
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

# Çevresel değişkenlerden veritabanı bağlantı bilgilerini al
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_DATABASE = os.getenv("DB_DATABASE")

def get_db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )
