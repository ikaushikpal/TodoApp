# TodoApp - FastAPI

## **Setup Instructions**

### **1. Clone the Repository**
```sh
git clone <repository-url>
cd TodoApp
```

### **2. Create a Virtual Environment**
```sh
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate  # On Windows
```

### **3. Install Dependencies**
```sh
pip install -r requirements.txt
```

### **4. Configure Database**
Update your `app/config.py` with the correct **MySQL** database connection:
```python
DATABASE_URL = "mysql+pymysql://username:password@localhost/todo_app_python"
```

### **5. Initialize Alembic (Database Migrations)**
#### **Generate Migration**
```sh
alembic revision --autogenerate -m "Initial migration"
```

#### **Apply Migration**
```sh
alembic upgrade head
```

### **6. Run the FastAPI Server**
```sh
uvicorn app.main:app --reload
```

### **7. Access API Docs**
- Open **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- Open **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### **8. Run Tests** (If applicable)
```sh
pytest tests/
```

