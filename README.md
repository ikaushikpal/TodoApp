# TodoApp - FastAPI Setup Instructions

## 1. Clone the Repository
```bash
git clone https://github.com/ikaushikpal/TodoApp.git
cd TodoApp
```

## 2. Create a Virtual Environment
```bash
python -m venv .venv
source .venv/bin/activate # On macOS/Linux
```
OR
```bash
.venv\Scripts\activate # On Windows
```

## 3. Install Dependencies
```bash
pip install -r requirements.txt
```

## 4. Configure Environment Variables
Rename example.env to .env:
```bash
mv example.env .env
```

Update the .env file with your actual values:
```
# Database Configuration
HOST=localhost
PORT=3306
USER=root
PASSWORD=your_database_password
DATABASE=todo_app_python

# JWT Configuration
JWT_SECRET_KEY=supersecretkey123
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
```

Rename example.alembic.ini to alembic.ini:
```bash
mv example.alembic.ini alembic.ini
```

Update the sqlalchemy.url in alembic.ini with your MySQL connection URL:
```ini
sqlalchemy.url = mysql+pymysql://username:password@localhost/todo_app_python
```

## 5. Initialize Alembic (Database Migrations)
Generate a migration:
```bash
alembic revision --autogenerate -m "Initial migration"
```

Apply the migration:
```bash
alembic upgrade head
```

## 6. Add Full-Text Search Indexes
Run the following MySQL queries to enable full-text search on the users and todos tables:

Full-Text Index for users Table:
```sql
ALTER TABLE users ADD FULLTEXT(id, username, email, first_name, last_name, country_code, phone_number);
```

Full-Text Index for todos Table:
```sql
CREATE FULLTEXT INDEX todos_title_IDX ON todo_app_python.todos (title, description);
```

## 7. Run the FastAPI Server
Start the FastAPI server in reload mode (automatically reloads on code changes):
```bash
uvicorn main:app --reload
```

Have configured logs using python logger. So if don't want to UNICORN info logs, then use the following command.
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level error --reload
```

for production deployment use bellow command
```bash
gunicorn -w 4 -k uvicorn.workers.UvicornWorker --keep-alive 5 main:app
```

## 8. Access API Docs
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc


## Summary of Changes
- **Environment Configuration:**
  - Renamed example.env to .env and updated it with your actual values.
  - Renamed example.alembic.ini to alembic.ini and updated the sqlalchemy.url.
- **Database Setup:**
  - Applied Alembic migrations to initialize the database schema.
  - Added full-text search indexes for the users and todos tables.
- **Running the Application:**
  - Started the FastAPI server in reload mode for local development.