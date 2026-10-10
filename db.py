
import psycopg
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")


def create_table():
    conn = psycopg.connect(
        host="localhost",
        port=5432,
        dbname="mydatabase",
        user="postgres",
        password=SECRET_KEY
    )

    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS Users (
                    id SERIAL PRIMARY KEY,
                    FirstName VARCHAR(100) NOT NULL,
                    LastName VARCHAR(100) NOT NULL,
                    age INTEGER NOT NULL,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password TEXT NOT NULL
                );
            """)

        conn.commit()
        print("Users table created successfully")

    finally:
        conn.close()


if __name__ == "__main__":
    create_table()