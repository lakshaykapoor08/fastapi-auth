# FastAPI Authentication API

A complete, production-ready authentication system built with FastAPI, PostgreSQL, and JWT tokens. Features include user registration, login, refresh tokens, password management, and account deletion.

## 🚀 Features

- ✅ User Registration with email & username validation
- ✅ JWT-based Authentication (Access & Refresh Tokens)
- ✅ "Remember Me" functionality with long-lived refresh tokens
- ✅ Password hashing with bcrypt
- ✅ Token refresh mechanism
- ✅ Password change with verification
- ✅ Logout from single device
- ✅ Logout from all devices
- ✅ Account deletion
- ✅ Protected endpoints with role-based access
- ✅ PostgreSQL database with SQLAlchemy ORM
- ✅ Automatic API documentation (Swagger UI & ReDoc)
- ✅ CORS middleware configuration
- ✅ Request timing middleware
- ✅ Comprehensive error handling

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## 🔧 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.9+**
- **PostgreSQL 12+**
- **pip** (Python package manager)
- **Git**

## 📦 Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/fastapi-auth.git
cd fastapi-auth
```

### 2. Create a virtual environment

**Windows:**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

**Option A: Using requirements.txt**

```bash
pip install -r requirements.txt
```

**Option B: Using pyproject.toml**

```bash
pip install -e .
```

### 4. Install development dependencies (optional)

```bash
pip install -e ".[dev]"
```

## ⚙️ Configuration

### 1. Create a `.env` file

Create a `.env` file in the project root directory:

```bash
cp .env.example .env
```

### 2. Configure environment variables

Edit the `.env` file with your settings:

```env
# Database Configuration
DATABASE_URL=postgresql+psycopg://postgres:your_password@localhost:5432/fastapi_auth

# Security
SECRET_KEY=your-secret-key-here-generate-with-openssl
ALGORITHM=HS256

# Token Expiration
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=30

# Application Settings
APP_NAME=FastAPI Authentication API
DEBUG=False
```

### 3. Generate a secure SECRET_KEY

**Using OpenSSL:**

```bash
openssl rand -hex 32
```

**Using Python:**

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Copy the generated key and paste it into your `.env` file.

## 🗄️ Database Setup

### 1. Create PostgreSQL Database

**Using psql:**

```bash
psql -U postgres
CREATE DATABASE fastapi_auth;
\q
```

**Using pgAdmin:**

- Right-click on "Databases"
- Select "Create" → "Database"
- Name: `fastapi_auth`
- Click "Save"

### 2. Create Database Tables

The application will automatically create tables on startup. To manually create them:

```bash
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 3. Verify Database Connection

```bash
python test_database.py
```

## 🏃 Running the Application

### Method 1: Using Command Scripts (Recommended)

**If installed with `pip install -e .`:**

```bash
dev      # Development server with hot reload
start    # Production server
```

### Method 2: Using Batch Files (Windows)

```bash
dev      # Development server
start    # Production server
```

### Method 3: Using Python Script

```bash
python app.scripts.py           # Development mode
python app.scripts.py prod      # Production mode
```

### Method 4: Direct uvicorn command

**Development:**

```bash
uvicorn app.main:app --reload
```

**Production:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📚 API Documentation

Once the server is running, access the interactive API documentation:

- **Swagger UI:** http://127.0.0.1:8000/docs
- **ReDoc:** http://127.0.0.1:8000/redoc
- **OpenAPI JSON:** http://127.0.0.1:8000/openapi.json

## 📁 Project Structure

```
fastapi-auth/
├── app/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # FastAPI application entry point
│   ├── config.py             # Configuration settings
│   ├── database.py           # Database connection & session
│   ├── models.py             # SQLAlchemy ORM models
│   ├── schemas.py            # Pydantic models for validation
│   ├── auth.py               # Authentication utilities
│   ├── auth_routes.py        # Authentication endpoints
│   └── scripts.py            # CLI scripts for running server
├── venv/                     # Virtual environment (not in git)
├── .env                      # Environment variables (not in git)
├── .env.example              # Example environment variables
├── .gitignore                # Git ignore rules
├── pyproject.toml            # Project metadata & dependencies
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── dev.bat                   # Development server script (Windows)
├── start.bat                 # Production server script (Windows)
├── run.py                    # Python runner script
└── test_database.py          # Database connection test
```

## 🔌 API Endpoints

### Public Endpoints

| Method | Endpoint           | Description                              |
| ------ | ------------------ | ---------------------------------------- |
| POST   | `/auth/register`   | Register a new user                      |
| POST   | `/auth/login`      | Login with OAuth2 (for Swagger UI)       |
| POST   | `/auth/login/json` | Login with JSON (supports refresh token) |
| POST   | `/auth/refresh`    | Refresh access token                     |

### Protected Endpoints (Require Authentication)

| Method | Endpoint                | Description                |
| ------ | ----------------------- | -------------------------- |
| GET    | `/auth/me`              | Get current user info      |
| POST   | `/auth/logout`          | Logout from current device |
| POST   | `/auth/logout-all`      | Logout from all devices    |
| PUT    | `/auth/change-password` | Change user password       |
| DELETE | `/auth/delete-account`  | Delete user account        |

### Health Check

| Method | Endpoint  | Description   |
| ------ | --------- | ------------- |
| GET    | `/`       | Root endpoint |
| GET    | `/health` | Health check  |

## 🧪 Testing

### Using Swagger UI

1. Navigate to http://127.0.0.1:8000/docs
2. Click **"Authorize"** button
3. Enter your username and password
4. Leave `client_id` and `client_secret` empty
5. Click **"Authorize"**
6. Test protected endpoints

### Using cURL

**Register a user:**

```bash
curl -X POST "http://127.0.0.1:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!"
  }'
```

**Login:**

```bash
curl -X POST "http://127.0.0.1:8000/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "johndoe",
    "password": "SecurePass123!",
    "remember_me": true
  }'
```

**Get current user (requires token):**

```bash
curl -X GET "http://127.0.0.1:8000/auth/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🚢 Deployment

### Environment Variables for Production

Update your `.env` file for production:

```env
DEBUG=False
DATABASE_URL=postgresql+psycopg://user:password@production-db:5432/fastapi_auth
SECRET_KEY=super-secure-production-key
```

### Using Gunicorn with Uvicorn Workers

```bash
pip install gunicorn
gunicorn app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🔐 Security Best Practices

- ✅ Always use HTTPS in production
- ✅ Keep `SECRET_KEY` secure and rotate regularly
- ✅ Use environment variables for sensitive data
- ✅ Enable rate limiting for authentication endpoints
- ✅ Implement account lockout after failed login attempts
- ✅ Use strong password requirements
- ✅ Regularly update dependencies
- ✅ Enable CORS only for trusted domains in production

## 🛠️ Troubleshooting

### Database Connection Error

**Problem:** `Database error occurred`

**Solution:**

1. Verify PostgreSQL is running
2. Check DATABASE_URL in `.env`
3. Ensure database exists: `CREATE DATABASE fastapi_auth;`
4. Test connection: `python test_database.py`

### bcrypt/passlib Error

**Problem:** `AttributeError: module 'bcrypt' has no attribute '__about__'`

**Solution:**

```bash
pip uninstall bcrypt passlib
pip install bcrypt==4.0.1 passlib[bcrypt]
```

### Module Not Found Error

**Problem:** `ModuleNotFoundError: No module named 'app'`

**Solution:**

- Ensure you're in the project root directory
- Activate virtual environment: `venv\Scripts\activate`
- Reinstall dependencies: `pip install -r requirements.txt`

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -am 'Add feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Lakshay Kapoor**

- GitHub: [@lakshaykapoor08](https://github.com/lakshaykapoor08)
- Email: lakshay.netweb@gmail.com

## 🙏 Acknowledgments

- FastAPI - Modern, fast web framework for building APIs
- SQLAlchemy - SQL toolkit and ORM
- Pydantic - Data validation using Python type annotations
- PostgreSQL - Powerful, open-source database
- Uvicorn - Lightning-fast ASGI server

## 📝 Changelog

### Version 1.0.0 (2025-01-XX)

- Initial release
- User registration and authentication
- JWT token management
- Refresh token functionality
- Password management
- Account deletion

---

**Made with ❤️ and FastAPI**
