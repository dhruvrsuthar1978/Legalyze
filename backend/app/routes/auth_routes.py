# app/routes/auth_routes.py

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.controllers.auth_controller import (
    register_user,
    login_user,
    get_current_user,
    refresh_access_token,
    logout_user,
    change_password,
    forgot_password,
    reset_password,
    update_profile
)
from app.models.user_model import (
    UserRegisterRequest,
    UserLoginRequest,
    TokenResponse,
    UserResponse,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest
)
from app.middleware.auth_middleware import verify_token

router = APIRouter(
    prefix="/auth",
    tags=["🔐 Authentication"]
)

limiter = Limiter(key_func=get_remote_address)


# ══════════════════════════════════════════════════════
# @route    POST /api/auth/register
# @desc     Register a new user account
# @access   Public
# @limit    5 requests per minute
# ══════════════════════════════════════════════════════
@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="""
    Creates a new user account in Legalyze.
    
    **Validations:**
    - Email must be unique and valid format
    - Password must be minimum 8 characters
    - Name must be 2–100 characters
    
    **Returns:** User profile + success message
    """
)
@limiter.limit("5/minute")
async def register(
    request: Request,
    payload: UserRegisterRequest
):
    return await register_user(payload)


# ══════════════════════════════════════════════════════
# @route    POST /api/auth/login
# @desc     Authenticate user and get JWT tokens
# @access   Public
# @limit    10 requests per minute
# ══════════════════════════════════════════════════════
@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login and receive access + refresh tokens",
    description="""
    Authenticates the user with email and password.
    
    **Returns:**
    - `access_token` — valid for **1 hour**
    - `refresh_token` — valid for **7 days**
    - `token_type` — Bearer
    
    Use the `access_token` in the `Authorization: Bearer <token>` header
    for all protected routes.
    """
)
@limiter.limit("10/minute")
async def login(
    request: Request,
    payload: UserLoginRequest
):
    return await login_user(payload)


# ══════════════════════════════════════════════════════
# @route    GET /api/auth/me
# @desc     Get currently authenticated user profile
# @access   Private (Bearer Token Required)
# ══════════════════════════════════════════════════════
@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current logged-in user profile",
    description="""
    Fetches the profile of the currently authenticated user.
    
    **Requires:** Valid `Authorization: Bearer <token>` header.
    
    **Returns:** Full user profile including name, email, and account metadata.
    """
)
async def get_profile(
    current_user: dict = Depends(verify_token)
):
    return await get_current_user(current_user)


# ══════════════════════════════════════════════════════
# @route    PUT /api/auth/me/update
# @desc     Update user profile details
# @access   Private
# ══════════════════════════════════════════════════════
@router.put(
    "/me/update",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="""
    Allows the authenticated user to update their profile details.
    
    **Updatable fields:** name, profile_picture
    
    **Note:** Email and password cannot be changed through this endpoint.
    Use `/change-password` for password updates.
    """
)
async def update_user_profile(
    payload: UpdateProfileRequest,
    current_user: dict = Depends(verify_token)
):
    return await update_profile(payload, current_user)


# ══════════════════════════════════════════════════════
# @route    POST /api/auth/refresh
# @desc     Refresh expired access token using refresh token
# @access   Public (Refresh Token Required)
# @limit    10 requests per minute
# ══════════════════════════════════════════════════════
@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="""
    Generates a new `access_token` using a valid `refresh_token`.
    
    Use this endpoint when the access token expires (after 1 hour)
    to avoid requiring the user to log in again.
    
    **Body:** `{ "refresh_token": "<your_refresh_token>" }`
    """
)
@limiter.limit("10/minute")
async def refresh_token(
    request: Request,
    refresh_token: str
):
    return await refresh_access_token(refresh_token)


# ══════════════════════════════════════════════════════
# @route    POST /api/auth/logout
# @desc     Logout user and blacklist current token
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout current user",
    description="""
    Logs out the current user by:
    - Invalidating the active access token (token blacklisting)
    - Recording logout timestamp in the database
    
    Subsequent requests using the same token will receive **401 Unauthorized**.
    """
)
async def logout(
    current_user: dict = Depends(verify_token)
):
    return await logout_user(current_user)


# ══════════════════════════════════════════════════════
# @route    POST /api/auth/change-password
# @desc     Change password for authenticated user
# @access   Private
# ══════════════════════════════════════════════════════
@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    description="""
    Allows an authenticated user to change their password.
    
    **Requires:**
    - `current_password` — existing password for verification
    - `new_password` — new password (min 8 characters)
    - `confirm_password` — must match `new_password`
    
    All active sessions will be invalidated after a successful change.
    """
)
async def change_user_password(
    payload: ChangePasswordRequest,
    current_user: dict = Depends(verify_token)
):
    return await change_password(payload, current_user)


# ══════════════════════════════════════════════════════
# @route    POST /api/auth/forgot-password
# @desc     Send password reset email
# @access   Public
# @limit    3 requests per minute
# ══════════════════════════════════════════════════════
@router.post(
    "/forgot-password",
    status_code=status.HTTP_200_OK,
    summary="Send password reset email",
    description="""
    Sends a password reset link to the user's registered email address.
    
    **Flow:**
    1. User submits their email
    2. System generates a one-time reset token (expires in **15 minutes**)
    3. Reset link is emailed to the user
    
    For security, this endpoint always returns success even if the email
    is not found in the system (prevents email enumeration attacks).
    """
)
@limiter.limit("3/minute")
async def forgot_user_password(
    request: Request,
    payload: ForgotPasswordRequest
):
    return await forgot_password(payload)


# ══════════════════════════════════════════════════════
# @route    POST /api/auth/reset-password
# @desc     Reset password using token from email
# @access   Public
# @limit    5 requests per minute
# ══════════════════════════════════════════════════════
@router.post(
    "/reset-password",
    status_code=status.HTTP_200_OK,
    summary="Reset password using reset token",
    description="""
    Resets the user's password using the token received via email.
    
    **Requires:**
    - `reset_token` — One-time token from the reset email
    - `new_password` — New password (min 8 characters)
    - `confirm_password` — Must match `new_password`
    
    Token is single-use and expires after **15 minutes**.
    """
)
@limiter.limit("5/minute")
async def reset_user_password(
    request: Request,
    payload: ResetPasswordRequest
):
    return await reset_password(payload)