from fastapi import APIRouter, Depends, Query, status
from typing import Optional

from app.controllers.admin_controller import (
    get_admin_audit_logs,
    get_admin_users,
    update_admin_user_role,
    update_admin_user_status,
)
from app.middleware.auth_middleware import require_admin


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    summary="List users for admin management",
)
async def list_users(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    q: Optional[str] = Query(None, description="Search by name or email"),
    current_user: dict = Depends(require_admin),
):
    return await get_admin_users(page=page, limit=limit, query=q)


@router.patch(
    "/users/{user_id}/role",
    status_code=status.HTTP_200_OK,
    summary="Update a user's role",
)
async def change_user_role(
    user_id: str,
    role: str = Query(..., description="admin | user | lawyer | client"),
    current_user: dict = Depends(require_admin),
):
    return await update_admin_user_role(
        target_user_id=user_id,
        role=role,
        current_user=current_user,
    )


@router.patch(
    "/users/{user_id}/status",
    status_code=status.HTTP_200_OK,
    summary="Update a user's account status",
)
async def change_user_status(
    user_id: str,
    account_status: str = Query(..., alias="status", description="active | suspended"),
    current_user: dict = Depends(require_admin),
):
    return await update_admin_user_status(
        target_user_id=user_id,
        account_status=account_status,
        current_user=current_user,
    )


@router.get(
    "/audit-logs",
    status_code=status.HTTP_200_OK,
    summary="Fetch recent admin audit logs",
)
async def list_audit_logs(
    limit: int = Query(25, ge=1, le=100),
    current_user: dict = Depends(require_admin),
):
    return await get_admin_audit_logs(limit=limit)
