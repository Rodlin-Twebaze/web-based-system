import re
import uuid
from datetime import datetime, timezone

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import MetaData
from typing import cast, Any
from sqlalchemy.orm import Session

try:
    # If package is installed/imported as a module
    from server.database import get_db, init_db
    from server.models import Base, Complaint, User
except Exception:
    # Fallback for running module as a script (direct execution)
    from database import get_db, init_db
    from models import Base, Complaint, User

app = FastAPI()

try:
    engine = init_db()
    cast(MetaData, Base.metadata).create_all(bind=engine)
except SQLAlchemyError as exc:
    raise RuntimeError(f"Database connection failed: {exc}") from exc


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    role: str = Field(default="user")
    password: str = Field(..., min_length=6)
    confirm_password: str = Field(..., min_length=6)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1)
    username: str = Field(..., min_length=1)
    email: str = Field(..., min_length=1)
    role: str = Field(default="user")
    password: str = Field(..., min_length=6)


class UpdateUserRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    username: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, min_length=1)
    role: str | None = None
    password: str | None = Field(default=None, min_length=6)


class CreateComplaintRequest(BaseModel):
    created_by_user_id: uuid.UUID
    complaint_type: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="open")


class UpdateComplaintRequest(BaseModel):
    created_by_user_id: uuid.UUID | None = None
    complaint_type: str | None = Field(default=None, min_length=1)
    message: str | None = Field(default=None, min_length=1, max_length=255)
    status: str | None = None
    assigned_to_user_id: uuid.UUID | None = None


def _normalize_role(role: str) -> str:
    normalized_role = role.strip().lower()
    if normalized_role not in {"admin", "user"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Role must be either 'admin' or 'user'")
    return normalized_role


def _normalize_status(complaint_status: str) -> str:
    normalized_status = complaint_status.strip().lower()
    if normalized_status not in {"open", "pending", "closed"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Status must be one of 'open', 'pending', 'closed'",
        )
    return normalized_status


def _serialize_user(user: User) -> dict[str, Any]:
    return {
        "id": str(user.id),
        "name": user.name,
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def _get_user_or_404(db: Session, user_id: uuid.UUID) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


def _serialize_complaint(complaint: Complaint) -> dict[str, Any]:
    return {
        "id": str(complaint.id),
        "created_by_user_id": str(complaint.created_by_user_id),
        "complaint_type": complaint.complaint_type,
        "message": complaint.message,
        "status": complaint.status,
        "assigned_to_user_id": str(complaint.assigned_to_user_id) if complaint.assigned_to_user_id else None,
        "date_created": complaint.date_created,
        "date_updated": complaint.date_updated,
    }


def _get_complaint_or_404(db: Session, complaint_id: uuid.UUID) -> Complaint:
    complaint = db.query(Complaint).filter(Complaint.id == complaint_id).first()
    if not complaint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    return complaint


@app.get("/")
def health_check():
    return {"message": "Complaint system API is running"}


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if payload.password != payload.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    role = _normalize_role(payload.role)
    user = User(
        name=payload.name.strip(),
        username=payload.username.strip(),
        email=email,
        role=role,
    )
    user.set_password(payload.password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        },
    }


@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()

    if not user or not user.verify_password(payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    cast(Any, user).updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return {
        "message": "User logged in successfully",
        "user": {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "updated_at": user.updated_at,
        },
    }


# User routes
@app.get("/users")
def get_users(
    name: str | None = None,
    username: str | None = None,
    email: str | None = None,
    role: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(User)
    if name:
        query = query.filter(User.name.ilike(f"%{name.strip()}%"))
    if username:
        query = query.filter(User.username == username.strip())
    if email:
        query = query.filter(User.email == email.strip().lower())
    if role:
        query = query.filter(User.role == _normalize_role(role))

    users = query.all()
    return {"message": "List of users", "users": [_serialize_user(user) for user in users]}


@app.get("/users/{user_id}")
def get_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    return {"message": f"Details of user {user_id}", "user": _serialize_user(user)}


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: CreateUserRequest, db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    username = payload.username.strip()
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")

    role = _normalize_role(payload.role)
    user = User(
        name=payload.name.strip(),
        username=username,
        email=email,
        role=role,
    )
    user.set_password(payload.password)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created", "user": _serialize_user(user)}


@app.patch("/users/{user_id}")
def update_user(user_id: uuid.UUID, payload: UpdateUserRequest, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)

    if payload.email is not None:
        email = payload.email.strip().lower()
        if db.query(User).filter(User.email == email, User.id != user_id).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
        cast(Any, user).email = email

    if payload.username is not None:
        username = payload.username.strip()
        if db.query(User).filter(User.username == username, User.id != user_id).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already taken")
        cast(Any, user).username = username

    if payload.name is not None:
        cast(Any, user).name = payload.name.strip()

    if payload.role is not None:
        cast(Any, user).role = _normalize_role(payload.role)

    if payload.password is not None:
        user.set_password(payload.password)

    cast(Any, user).updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(user)

    return {"message": f"User {user_id} updated", "user": _serialize_user(user)}


@app.delete("/users/{user_id}")
def delete_user(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    db.delete(user)
    db.commit()

    return {"message": f"User {user_id} deleted"}


# Complaint routes
@app.get("/complaints")
def get_complaints(
    status: str | None = Query(default=None),
    complaint_type: str | None = None,
    created_by_user_id: uuid.UUID | None = None,
    assigned_to_user_id: uuid.UUID | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Complaint)
    if status:
        query = query.filter(Complaint.status == _normalize_status(status))
    if complaint_type:
        query = query.filter(Complaint.complaint_type.ilike(f"%{complaint_type.strip()}%"))
    if created_by_user_id:
        query = query.filter(Complaint.created_by_user_id == created_by_user_id)
    if assigned_to_user_id:
        query = query.filter(Complaint.assigned_to_user_id == assigned_to_user_id)

    complaints = query.all()
    return {"message": "List of complaints", "complaints": [_serialize_complaint(c) for c in complaints]}


@app.get("/complaints/{complaint_id}")
def get_complaint(complaint_id: uuid.UUID, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, complaint_id)
    return {"message": f"Details of complaint {complaint_id}", "complaint": _serialize_complaint(complaint)}


@app.post("/complaints", status_code=status.HTTP_201_CREATED)
def create_complaint(payload: CreateComplaintRequest, db: Session = Depends(get_db)):
    creator = _get_user_or_404(db, payload.created_by_user_id)

    complaint = Complaint(
        created_by_user_id=creator.id,
        complaint_type=payload.complaint_type.strip(),
        message=payload.message.strip(),
        status=_normalize_status(payload.status),
    )
    db.add(complaint)
    db.commit()
    db.refresh(complaint)

    return {"message": "Complaint created", "complaint": _serialize_complaint(complaint)}


@app.patch("/complaints/{complaint_id}")
def update_complaint(complaint_id: uuid.UUID, payload: UpdateComplaintRequest, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, complaint_id)
    updates = payload.model_dump(exclude_unset=True)

    if "created_by_user_id" in updates:
        creator = _get_user_or_404(db, updates["created_by_user_id"])
        cast(Any, complaint).created_by_user_id = creator.id

    if "complaint_type" in updates:
        cast(Any, complaint).complaint_type = updates["complaint_type"].strip()

    if "message" in updates:
        cast(Any, complaint).message = updates["message"].strip()

    if "status" in updates:
        cast(Any, complaint).status = _normalize_status(updates["status"])

    if "assigned_to_user_id" in updates:
        assigned_to_user_id = updates["assigned_to_user_id"]
        if assigned_to_user_id is not None:
            assignee = _get_user_or_404(db, assigned_to_user_id)
            assigned_to_user_id = assignee.id
        cast(Any, complaint).assigned_to_user_id = assigned_to_user_id

    cast(Any, complaint).date_updated = datetime.now(timezone.utc)
    db.commit()
    db.refresh(complaint)

    return {"message": f"Complaint {complaint_id} updated", "complaint": _serialize_complaint(complaint)}


@app.delete("/complaints/{complaint_id}")
def delete_complaint(complaint_id: uuid.UUID, db: Session = Depends(get_db)):
    complaint = _get_complaint_or_404(db, complaint_id)
    db.delete(complaint)
    db.commit()

    return {"message": f"Complaint {complaint_id} deleted"}

