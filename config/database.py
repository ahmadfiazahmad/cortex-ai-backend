import os
import psycopg
from dotenv import load_dotenv

load_dotenv()


def connect_to_database():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )





if __name__ == "__main__":
    try:
        connection = connect_to_database()
        print("Database connected successfully!")
        connection.close()
    except Exception as e:
        print(f"Database connection failed: {e}")