import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "rdnc"),
        database=os.getenv("DB_NAME", "food_analyzer"),
        connection_timeout=10
    )
    return connection