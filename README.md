# Nambikkai Support Backend

This is the FastAPI backend for the Nambikkai Support website.

## Features
- User Registration & Login (JWT Authentication)
- Data fetch for NGOs and Lawyers
- Appointment Booking
- User Dashboard API

## Setup Instructions

1. **Prerequisites**:
   - Python 3.8+
   - pip

2. **Installation**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Running the Server**:
   ```bash
   python -m uvicorn main:app --reload
   ```
   The server will start at `http://127.0.0.1:8000`.

## API Documentation
Once the server is running, you can access the interactive API docs at:
- Swagger UI: `http://127.0.0.1:8000/docs`
- Redoc: `http://127.0.0.1:8000/redoc`

## Database
By default, this uses SQLite (`nambikkai.db`). You can switch to PostgreSQL by updating the `DATABASE_URL` in the `.env` file.
