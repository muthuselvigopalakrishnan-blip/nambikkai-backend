from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import models, schemas, auth, database
from database import engine, get_db
from typing import List, Optional
import os
from dotenv import load_dotenv
from fastapi_mail import FastMail, ConnectionConfig, MessageSchema, MessageType

load_dotenv()

# Email Configuration
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 587)),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_FROM_NAME="Nambikkai Support",
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS", "True") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS", "False") == "True",
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

async def send_email_async(subject: str, email_to: str, body: dict):
    # Note: For simple text/html without separate template files:
    html_content = f"""
    <html>
    <body>
        <p>Hi {body.get('name')},</p>
        <p>{body.get('message')}</p>
        <p><b>Appointment Details:</b></p>
        <ul>
            <li>Date: {body.get('date')}</li>
            <li>Provider: {body.get('provider')}</li>
            <li>Status: {body.get('status')}</li>
        </ul>
        <br>
        <p>Support Team, Nambikkai</p>
    </body>
    </html>
    """
    
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)

# Create tables (Only if they don't exist)
models.Base.metadata.create_all(bind=engine)

class StatusUpdate(schemas.BaseModel):
    status: str


# Seed Initial Data (Only if empty)
def seed_data():
    db = database.SessionLocal()
    try:
        # Check if NGOs table is empty
        if db.query(models.NGO).count() == 0:
            initial_ngos = [
                {
                    "name": "Aasara Foundation",
                    "description": "Supporting victims of honor killing.",
                },
                {"name": "Dhanak", "description": "Promoting right to choose."},
                {"name": "DHRDNet", "description": "Human rights protection."},
                {
                    "name": "Evidence Madurai",
                    "description": "Monitoring social justice.",
                },
                {"name": "Love Commando", "description": "Protecting love birds."},
                {"name": "Manjhi", "description": "Empowering communities."},
            ]
            for ngo_data in initial_ngos:
                db.add(models.NGO(**ngo_data))
            db.commit()

        # Check if Lawyers table is empty
        if db.query(models.Lawyer).count() == 0:
            initial_lawyers = [
                {"name": "Anand Grover", "quote": "Honor killing is a crime."},
                {"name": "Colin Gonsalves", "quote": "Say NO to violence."},
                {"name": "Indira Jaising", "quote": "We must support victims."},
                {"name": "Kavita Srivastava", "quote": "Education can stop it."},
                {"name": "Rebecca John", "quote": "Strong law is needed."},
                {"name": "Vrinda Grover", "quote": "Everyone has rights."},
            ]
            for lawyer_data in initial_lawyers:
                db.add(models.Lawyer(**lawyer_data))
            db.commit()
    finally:
        db.close()


seed_data()

app = FastAPI(title="Nambikkai Support Backend")

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    body = await request.body()
    print(f"422 Error: {exc}")
    print(f"Request Body: {body.decode()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": body.decode()},
    )

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Root endpoint
@app.get("/")
def read_root():
    return {"message": "Welcome to Nambikkai Support Backend API"}


# Auth Endpoints
@app.post("/api/auth/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        full_name=user.full_name, email=user.email, hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@app.post("/api/auth/login")
def login(
    user: schemas.UserCreate, db: Session = Depends(get_db)
):  # Using UserCreate for convenience, normally a Login schema
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = auth.create_access_token(data={"sub": db_user.email})
    return {"access_token": access_token, "token_type": "bearer", "user": db_user}


# NGO Endpoints
@app.get("/api/ngos", response_model=List[schemas.NGO])
def get_ngos(db: Session = Depends(get_db)):
    return db.query(models.NGO).all()


@app.get("/api/ngos/{ngo_id}", response_model=schemas.NGO)
def get_ngo(ngo_id: int, db: Session = Depends(get_db)):
    ngo = db.query(models.NGO).filter(models.NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    return ngo


# Lawyer Endpoints
@app.get("/api/lawyers", response_model=List[schemas.Lawyer])
def get_lawyers(db: Session = Depends(get_db)):
    return db.query(models.Lawyer).all()


@app.get("/api/lawyers/{lawyer_id}", response_model=schemas.Lawyer)
def get_lawyer(lawyer_id: int, db: Session = Depends(get_db)):
    lawyer = db.query(models.Lawyer).filter(models.Lawyer.id == lawyer_id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    return lawyer


# Appointment Endpoints
@app.post("/api/appointments", response_model=schemas.Appointment)
async def create_appointment(
    appointment: schemas.AppointmentCreate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_appointment = models.Appointment(**appointment.dict())
    db.add(db_appointment)
    db.commit()
    db.refresh(db_appointment)
    
    # Send Email in background
    email_body = {
        "name": db_appointment.full_name,
        "date": str(db_appointment.appointment_date),
        "provider": db_appointment.provider_name,
        "status": db_appointment.status,
        "message": f"Your appointment request has been received by {db_appointment.provider_name}. Please wait for approval."
    }
    background_tasks.add_task(send_email_async, "Appointment Received - Nambikkai", db_appointment.email, email_body)

    return db_appointment


@app.get("/api/appointments", response_model=List[schemas.Appointment])
def get_appointments(
    email: Optional[str] = None,
    provider_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(models.Appointment)
    if email:
        query = query.filter(models.Appointment.email == email)
    if provider_name:
        query = query.filter(models.Appointment.provider_name == provider_name)
    return query.all()


@app.get("/api/appointments/ngo/{ngo_id}", response_model=List[schemas.Appointment])
def get_appointments_by_ngo(ngo_id: int, db: Session = Depends(get_db)):
    ngo = db.query(models.NGO).filter(models.NGO.id == ngo_id).first()
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.appointment_type == "NGO",
            models.Appointment.provider_name == ngo.name,
        )
        .all()
    )


@app.get(
    "/api/appointments/lawyer/{lawyer_id}", response_model=List[schemas.Appointment]
)
def get_appointments_by_lawyer(lawyer_id: int, db: Session = Depends(get_db)):
    lawyer = db.query(models.Lawyer).filter(models.Lawyer.id == lawyer_id).first()
    if not lawyer:
        raise HTTPException(status_code=404, detail="Lawyer not found")
    return (
        db.query(models.Appointment)
        .filter(
            models.Appointment.appointment_type == "LAWYER",
            models.Appointment.provider_name == lawyer.name,
        )
        .all()
    )


@app.patch("/api/appointments/{appointment_id}/status", response_model=schemas.Appointment)
async def update_appointment_status(
    appointment_id: int, 
    status_update: StatusUpdate, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    db_appointment = (
        db.query(models.Appointment)
        .filter(models.Appointment.id == appointment_id)
        .first()
    )
    if not db_appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    new_status = status_update.status
    if not new_status:
        raise HTTPException(status_code=400, detail="Status is required")

    db_appointment.status = new_status
    db.commit()
    db.refresh(db_appointment)
    
    # Send Notification Email
    email_body = {
        "name": db_appointment.full_name,
        "date": str(db_appointment.appointment_date),
        "provider": db_appointment.provider_name,
        "status": db_appointment.status,
        "message": f"Your appointment status has been updated to: {db_appointment.status}."
    }
    background_tasks.add_task(send_email_async, f"Appointment {db_appointment.status} - Nambikkai", db_appointment.email, email_body)

    return db_appointment


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
