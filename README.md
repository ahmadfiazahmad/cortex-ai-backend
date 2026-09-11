# Cortex AI Backend

Backend project developed as part of the **Zyro Internship Program – Week 2**.

This week implements a basic **JWT-based authentication system** using Python, FastAPI, and PostgreSQL.

## Technologies Used

- Python
- FastAPI
- Uvicorn
- PostgreSQL
- Psycopg
- bcrypt
- PyJWT
- python-dotenv
- Git
- GitHub

## Project Structure

```text
cortex-ai-backend/
│
├── config/
│   └── database.py
│
├── controllers/
│   └── auth_controller.py
│
├── middleware/
│   ├── auth_middleware.py
│   ├── error_handler.py
│   └── request_logger.py
│
├── models/
│   └── user.py
│
├── routes/
│   ├── auth.py
│   └── health.py
│
├── utils/
│
├── .env
├── .gitignore
├── main.py
├── README.md
└── requirements.txt