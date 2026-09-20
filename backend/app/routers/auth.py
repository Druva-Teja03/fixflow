from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models import User, UserRole
from backend.app.schemas import UserRegisterRequest, UserLoginRequest, UserResponse, TokenResponse
from backend.app.security import get_password_hash, verify_password, create_access_token
from backend.app.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register_student(payload: UserRegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new student account.
    Public registration automatically assigns the student role.
    """
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email address already exists.",
        )

    # Hash the password
    hashed_pwd = get_password_hash(payload.password)

    # Create student user
    new_user = User(
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        password_hash=hashed_pwd,
        role=UserRole.STUDENT,
        team=None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate access token
    access_token = create_access_token(
        subject=new_user.user_id,
        role=new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role),
    )

    user_resp = UserResponse(
        user_id=new_user.user_id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role.value if hasattr(new_user.role, "value") else str(new_user.role),
        team=new_user.team,
        created_at=new_user.created_at,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_resp,
    )


@router.post("/login", response_model=TokenResponse)
def login_user(payload: UserLoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate a user (student, admin, staff) with email and password.
    Returns a JWT Bearer access token valid for 12 hours.
    """
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_role_str = user.role.value if hasattr(user.role, "value") else str(user.role)

    # Generate JWT token
    access_token = create_access_token(
        subject=user.user_id,
        role=user_role_str,
    )

    user_resp = UserResponse(
        user_id=user.user_id,
        name=user.name,
        email=user.email,
        role=user_role_str,
        team=user.team,
        created_at=user.created_at,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user_resp,
    )


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """
    Get profile details of the currently authenticated user.
    """
    user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
    return UserResponse(
        user_id=current_user.user_id,
        name=current_user.name,
        email=current_user.email,
        role=user_role_str,
        team=current_user.team,
        created_at=current_user.created_at,
    )
