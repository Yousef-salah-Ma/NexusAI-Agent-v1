import os
import psycopg
from sec import password_hash , verify_hash  , create_access_token
from dotenv import load_dotenv
from psycopg.errors import UniqueViolation

from fastapi import HTTPException
from schame import login_users ,  Create_Account 
import os

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")



def Register(
    FirstName: str,
    LastName: str,
    age: int,
    email: str,
    password: str
):
    hashed_password = password_hash(password)

    try:
        with psycopg.connect(
            host="localhost",
            port=5432,
            dbname="mydatabase",
            user="postgres",
            password=SECRET_KEY
        ) as conn:

            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO Users
                        (FirstName, LastName, age, email, password)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        FirstName,
                        LastName,
                        age,
                        email,
                        hashed_password
                    )
                )

        return {"message": "User registered successfully"}

    except UniqueViolation:
        raise HTTPException(
            status_code=409,
            detail="Email already exists"
        )
def login(password, in_email):

    conn = psycopg.connect(
        host="localhost",
        port=5432,
        dbname="mydatabase",
        user="postgres",
        password=SECRET_KEY
    )

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM Users WHERE email = %s",
            (in_email,)
        )

        user = cursor.fetchone()

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        user_id, first_name, last_name, age, email, password_hash = user

        verify_password = verify_hash(password, password_hash)

        if not verify_password:
            raise HTTPException(
                status_code=401,
                detail="Invalid email or password"
            )

        token = create_access_token(
            user_id,
            first_name
        )

        return {
    "access_token": token,
    "token_type": "bearer"
}

    finally:
        cursor.close()
        conn.close()