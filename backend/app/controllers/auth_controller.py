# app/controllers/auth_controller.py

from fastapi import HTTPException, status
from app.config.database import get_database
from app.models.user_model import (
    UserRegisterRequest,
    UserLoginRequest,
    ChangePasswordRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    UpdateProfileRequest
)
from app.utils.jwt_utils import (
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.utils.hash_utils import hash_password, verify_password
from app.utils.email_utils import send_password_reset_email
from datetime import datetime, timedelta
from bson import ObjectId
import secrets
import logging

logger = logging.getLogger("legalyze.auth")


# ══════════════════════════════════════════════════════════════════
# USER REGISTRATION
# ══════════════════════════════════════════════════════════════════

async def register_user(payload: UserRegisterRequest) -> dict:
    """
    Registers a new user account.
    
    Validations:
    - Email uniqueness check
    - Password strength (handled by Pydantic model)
    - Password confirmation match (handled by Pydantic model)
    
    Returns:
        User profile response with success message
    """
    logger.info(f"Registration attempt | email={payload.email}")
    
    db = get_database()
    
    # Check if email already exists
    existing = await db["users"].find_one({"email": payload.email})
    if existing:
        logger.warning(f"Registration failed: email exists | {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error": "Email already registered",
                "email": payload.email,
                "suggestion": "Try logging in or use password reset if you forgot your password."
            }
        )
    
    # Force safe default role for public self-registration.
    # Privileged roles (admin/lawyer) must be assigned via admin APIs.
    assigned_role = "client"
    requested_role = str(payload.role or "").lower().strip()
    if requested_role and requested_role != assigned_role:
        logger.warning(
            f"Registration attempted with elevated/custom role, overriding | "
            f"email={payload.email}, requested_role={requested_role}, assigned_role={assigned_role}"
        )

    # Hash password
    hashed_pw = hash_password(payload.password)
    
    # Create user document
    new_user = {
        "name": payload.name,
        "email": payload.email,
        "password": hashed_pw,
        "role": assigned_role,
        "account_status": "active",
        "profile": {
            "phone": None,
            "organization": None,
            "job_title": None,
            "profile_picture": None
        },
        "created_at": datetime.utcnow(),
        "last_login": None,
        "email_verified": False,
        "rsa_private_key": None,    # Generated on first signature
        "rsa_public_key": None
    }
    
    result = await db["users"].insert_one(new_user)
    user_id = str(result.inserted_id)
    
    logger.info(f"User registered successfully | id={user_id}, email={payload.email}")
    
    return {
        "id": user_id,
        "name": new_user["name"],
        "email": new_user["email"],
        "role": new_user["role"],
        "account_status": new_user["account_status"],
        "created_at": new_user["created_at"],
        "message": "Account created successfully. Welcome to Legalyze!"
    }


# ══════════════════════════════════════════════════════════════════
# USER LOGIN
# ══════════════════════════════════════════════════════════════════

async def login_user(payload: UserLoginRequest) -> dict:
    """
    Authenticates user and returns JWT tokens.
    
    Security measures:
    - Password verification with bcrypt
    - Account status check (active/suspended)
    - Last login timestamp update
    - Remember me: extends refresh token to 30 days
    
    Returns:
        Access token (1h) + Refresh token (7d or 30d)
    """
    logger.info(f"Login attempt | email={payload.email}")
    
    db = get_database()
    
    # Fetch user
    user = await db["users"].find_one({"email": payload.email})
    
    if not user:
        logger.warning(f"Login failed: user not found | {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    # Verify password
    if not verify_password(payload.password, user["password"]):
        logger.warning(f"Login failed: wrong password | {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )
    
    # Check account status
    if user.get("account_status") != "active":
        logger.warning(
            f"Login blocked: account {user.get('account_status')} | {payload.email}"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is {user.get('account_status')}. Please contact support."
        )
    
    # Create tokens
    token_payload = {
        "sub": str(user["_id"]),
        "email": user["email"],
        "role": user.get("role", "user")
    }
    
    access_token = create_access_token(token_payload)
    
    # Remember me: 30 days refresh, else 7 days
    refresh_ttl_days = 30 if payload.remember_me else 7
    refresh_token = create_refresh_token(token_payload, ttl_days=refresh_ttl_days)
    
    # Update last login
    await db["users"].update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.utcnow()}}
    )
    
    logger.info(
        f"Login successful | "
        f"user_id={str(user['_id'])}, "
        f"remember_me={payload.remember_me}"
    )
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "Bearer",
        "expires_in": 3600   # 1 hour in seconds
    }


# ══════════════════════════════════════════════════════════════════
# GET CURRENT USER
# ══════════════════════════════════════════════════════════════════

async def get_current_user(current_user: dict) -> dict:
    """
    Fetches the authenticated user's profile.
    
    Args:
        current_user: JWT payload from verify_token middleware
    
    Returns:
        Full user profile with metadata
    """
    user_id = current_user["sub"]
    
    db = get_database()
    
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    
    if not user:
        logger.error(f"User not found in DB but has valid token | id={user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User account not found. Token may be invalid."
        )
    
    return {
        "id": str(user["_id"]),
        "name": user["name"],
        "email": user["email"],
        "role": user.get("role", "user"),
        "account_status": user.get("account_status", "active"),
        "profile": user.get("profile", {}),
        "created_at": user["created_at"],
        "last_login": user.get("last_login")
    }


# ══════════════════════════════════════════════════════════════════
# UPDATE PROFILE
# ══════════════════════════════════════════════════════════════════

async def update_profile(
    payload: UpdateProfileRequest,
    current_user: dict
) -> dict:
    """
    Updates the user's profile metadata.
    
    Updatable fields: name, phone, organization, job_title, profile_picture
    Email and password cannot be changed here.
    """
    user_id = current_user["sub"]
    
    db = get_database()
    
    update_fields = {}
    
    if payload.name is not None:
        update_fields["name"] = payload.name
    
    if payload.phone is not None:
        update_fields["profile.phone"] = payload.phone
    
    if payload.organization is not None:
        update_fields["profile.organization"] = payload.organization
    
    if payload.job_title is not None:
        update_fields["profile.job_title"] = payload.job_title
    
    if payload.profile_picture is not None:
        update_fields["profile.profile_picture"] = payload.profile_picture
    
    if not update_fields:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided to update."
        )
    
    result = await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        logger.warning(f"Profile update: no changes | user_id={user_id}")
    
    logger.info(f"Profile updated | user_id={user_id}, fields={list(update_fields.keys())}")
    
    # Fetch updated user
    return await get_current_user(current_user)


# ══════════════════════════════════════════════════════════════════
# REFRESH TOKEN
# ══════════════════════════════════════════════════════════════════

async def refresh_access_token(refresh_token: str) -> dict:
    """
    Issues a new access token using a valid refresh token.
    
    Validates:
    - Token signature and expiry
    - Token type (must be 'refresh')
    - User still exists and is active
    """
    payload = decode_token(refresh_token)
    
    db = get_database()
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )
    
    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token is not a refresh token."
        )
    
    # Verify user still exists and is active
    user = await db["users"].find_one({"_id": ObjectId(payload["sub"])})
    
    if not user or user.get("account_status") != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is no longer valid."
        )
    
    # Issue new access token
    new_access = create_access_token({
        "sub": payload["sub"],
        "email": payload.get("email"),
        "role": user.get("role", "user")
    })
    
    logger.info(f"Access token refreshed | user_id={payload['sub']}")
    
    return {
        "access_token": new_access,
        "refresh_token": refresh_token,   # Same refresh token
        "token_type": "Bearer",
        "expires_in": 3600
    }


# ══════════════════════════════════════════════════════════════════
# LOGOUT
# ══════════════════════════════════════════════════════════════════

async def logout_user(current_user: dict) -> dict:
    """
    Logs out the user by blacklisting the current token.
    
    Token blacklist stored in MongoDB with TTL index (auto-expires).
    """
    user_id = current_user["sub"]
    
    db = get_database()
    
    # Add token to blacklist (expires after 1 hour — access token TTL)
    await db["token_blacklist"].insert_one({
        "user_id": user_id,
        "logged_out_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(hours=1)
    })
    
    # Create TTL index on expires_at if not exists
    await db["token_blacklist"].create_index(
        "expires_at",
        expireAfterSeconds=0
    )
    
    logger.info(f"User logged out | user_id={user_id}")
    
    return {
        "success": True,
        "message": "Logged out successfully."
    }


# ══════════════════════════════════════════════════════════════════
# CHANGE PASSWORD
# ══════════════════════════════════════════════════════════════════

async def change_password(
    payload: ChangePasswordRequest,
    current_user: dict
) -> dict:
    """
    Changes the user's password after verifying the current password.
    
    Security:
    - Verifies current password
    - Checks new password strength (Pydantic)
    - Ensures new != current
    - Invalidates all sessions (token blacklist)
    """
    user_id = current_user["sub"]
    
    db = get_database()
    
    user = await db["users"].find_one({"_id": ObjectId(user_id)})
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    
    # Verify current password
    if not verify_password(payload.current_password, user["password"]):
        logger.warning(f"Change password failed: wrong current password | {user_id}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect."
        )
    
    # Hash new password
    new_hashed = hash_password(payload.new_password)
    
    # Update password
    await db["users"].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": new_hashed}}
    )
    
    # Invalidate all active sessions by blacklisting user ID
    await db["token_blacklist"].insert_one({
        "user_id": user_id,
        "logged_out_at": datetime.utcnow(),
        "reason": "password_changed",
        "expires_at": datetime.utcnow() + timedelta(days=7)
    })
    
    logger.info(f"Password changed successfully | user_id={user_id}")
    
    return {
        "success": True,
        "message": "Password changed successfully. Please log in again."
    }


# ══════════════════════════════════════════════════════════════════
# FORGOT PASSWORD
# ══════════════════════════════════════════════════════════════════

async def forgot_password(payload: ForgotPasswordRequest) -> dict:
    """
    Sends a password reset email with a one-time token.
    
    Security:
    - Always returns success (prevents email enumeration)
    - Token expires in 15 minutes
    - Single-use token (deleted after use)
    """
    logger.info(f"Password reset requested | email={payload.email}")
    
    db = get_database()
    
    user = await db["users"].find_one({"email": payload.email})
    
    # Always return success to prevent email enumeration
    if not user:
        logger.info(f"Reset email not found in DB: {payload.email} (silent success)")
        return {
            "success": True,
            "message": "If this email is registered, a reset link has been sent.",
            "email": payload.email
        }
    
    # Generate secure reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at  = datetime.utcnow() + timedelta(minutes=15)
    
    # Store reset token
    await db["password_resets"].insert_one({
        "user_id": str(user["_id"]),
        "email": payload.email,
        "token": reset_token,
        "created_at": datetime.utcnow(),
        "expires_at": expires_at,
        "used": False
    })
    
    # Create TTL index
    await db["password_resets"].create_index(
        "expires_at",
        expireAfterSeconds=0
    )
    
    # Send reset email
    try:
        await send_password_reset_email(
            email=payload.email,
            name=user["name"],
            reset_token=reset_token
        )
        logger.info(f"Reset email sent | email={payload.email}")
    except Exception as e:
        logger.error(f"Failed to send reset email: {e}")
        # Still return success to user (don't expose failure)
    
    return {
        "success": True,
        "message": "If this email is registered, a reset link has been sent.",
        "email": payload.email
    }


# ══════════════════════════════════════════════════════════════════
# RESET PASSWORD
# ══════════════════════════════════════════════════════════════════

async def reset_password(payload: ResetPasswordRequest) -> dict:
    """
    Resets password using the email-provided reset token.
    
    Validations:
    - Token exists and is not expired
    - Token has not been used
    - New password meets strength requirements
    """
    logger.info(f"Password reset attempt | token={payload.reset_token[:8]}...")
    
    db = get_database()
    
    # Find reset token
    reset_doc = await db["password_resets"].find_one({
        "token": payload.reset_token,
        "used": False,
        "expires_at": {"$gt": datetime.utcnow()}
    })
    
    if not reset_doc:
        logger.warning(f"Invalid/expired reset token: {payload.reset_token[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token. Please request a new one."
        )
    
    # Hash new password
    new_hashed = hash_password(payload.new_password)
    
    # Update password
    await db["users"].update_one(
        {"_id": ObjectId(reset_doc["user_id"])},
        {"$set": {"password": new_hashed}}
    )
    
    # Mark token as used
    await db["password_resets"].update_one(
        {"_id": reset_doc["_id"]},
        {"$set": {"used": True, "used_at": datetime.utcnow()}}
    )
    
    # Invalidate all sessions
    await db["token_blacklist"].insert_one({
        "user_id": reset_doc["user_id"],
        "logged_out_at": datetime.utcnow(),
        "reason": "password_reset",
        "expires_at": datetime.utcnow() + timedelta(days=7)
    })
    
    logger.info(f"Password reset successful | user_id={reset_doc['user_id']}")
    
    return {
        "success": True,
        "message": "Password reset successfully. Please log in with your new password."
    }
