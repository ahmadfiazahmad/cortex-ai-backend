import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import HTTPException, status

from config.database import connect_to_database
from models.user import UserCreate, UserLogin

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))


def register_user(user: UserCreate):
    hashed_password = bcrypt.hashpw(
        user.password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    try:
        with connect_to_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM users
                    WHERE email = %s
                    """,
                    (user.email,),
                )

                if cursor.fetchone():
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="Email is already registered",
                    )

                cursor.execute(
                    """
                    INSERT INTO users (name, email, password)
                    VALUES (%s, %s, %s)
                    RETURNING id, name, email, created_at
                    """,
                    (user.name, user.email, hashed_password),
                )

                created_user = cursor.fetchone()

        return {
            "id": created_user[0],
            "name": created_user[1],
            "email": created_user[2],
            "createdAt": created_user[3],
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user",
        )


def login_user(user: UserLogin):
    try:
        with connect_to_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, email, password, created_at
                    FROM users
                    WHERE email = %s
                    """,
                    (user.email,),
                )

                db_user = cursor.fetchone()

        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        password_matches = bcrypt.checkpw(
            user.password.encode("utf-8"),
            db_user[3].encode("utf-8"),
        )

        if not password_matches:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )

        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        )

        token_payload = {
            "user_id": db_user[0],
            "exp": expires_at,
        }

        token = jwt.encode(
            token_payload,
            JWT_SECRET,
            algorithm=JWT_ALGORITHM,
        )

        return {
            "access_token": token,
            "token_type": "bearer",
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed",
        )


def get_user_by_id(user_id: int):
    try:
        with connect_to_database() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, name, email, created_at
                    FROM users
                    WHERE id = %s
                    """,
                    (user_id,),
                )

                user = cursor.fetchone()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return {
            "id": user[0],
            "name": user[1],
            "email": user[2],
            "createdAt": user[3],
        }

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user",
        )