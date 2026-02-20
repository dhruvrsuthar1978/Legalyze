from datetime import UTC, datetime
from typing import Optional

from bson import ObjectId
from fastapi import HTTPException, status

from app.config.database import get_database


ALLOWED_ROLES = {"admin", "user", "lawyer", "client"}
ALLOWED_ACCOUNT_STATUSES = {"active", "suspended"}


async def _insert_audit_log(
    actor_user: dict,
    action: str,
    target_user_id: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    db = get_database()
    await db["audit_logs"].insert_one({
        "action": action,
        "actor_user_id": actor_user.get("sub"),
        "actor_email": actor_user.get("email"),
        "target_user_id": target_user_id,
        "details": details or {},
        "created_at": datetime.now(UTC),
    })


async def get_admin_users(page: int, limit: int, query: Optional[str]) -> dict:
    db = get_database()

    user_filter = {}
    if query:
        user_filter["$or"] = [
            {"name": {"$regex": query, "$options": "i"}},
            {"email": {"$regex": query, "$options": "i"}},
        ]

    total = await db["users"].count_documents(user_filter)
    skip = (page - 1) * limit

    cursor = (
        db["users"]
        .find(user_filter)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    users = await cursor.to_list(length=limit)

    user_ids = [str(u["_id"]) for u in users]
    contract_counts = {}
    if user_ids:
        counts = await db["contracts"].aggregate([
            {"$match": {"user_id": {"$in": user_ids}}},
            {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
        ]).to_list(length=500)
        contract_counts = {item["_id"]: item["count"] for item in counts}

    user_list = []
    for user in users:
        user_id = str(user["_id"])
        user_list.append({
            "id": user_id,
            "name": user.get("name"),
            "email": user.get("email"),
            "role": user.get("role", "user"),
            "account_status": user.get("account_status", "active"),
            "contracts": contract_counts.get(user_id, 0),
            "created_at": user.get("created_at"),
            "last_login": user.get("last_login"),
        })

    return {
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": (total + limit - 1) // limit,
        "users": user_list,
    }


async def update_admin_user_role(
    target_user_id: str,
    role: str,
    current_user: dict,
) -> dict:
    normalized_role = (role or "").strip().lower()
    if normalized_role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Role must be one of: {', '.join(sorted(ALLOWED_ROLES))}",
        )

    db = get_database()

    if target_user_id == current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own role from admin panel.",
        )

    try:
        target_oid = ObjectId(target_user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format.",
        )

    target_user = await db["users"].find_one({"_id": target_oid})
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    await db["users"].update_one(
        {"_id": target_oid},
        {"$set": {"role": normalized_role, "updated_at": datetime.now(UTC)}},
    )

    await _insert_audit_log(
        actor_user=current_user,
        action="user.role_updated",
        target_user_id=target_user_id,
        details={
            "old_role": target_user.get("role", "user"),
            "new_role": normalized_role,
            "target_email": target_user.get("email"),
        },
    )

    updated = await db["users"].find_one({"_id": target_oid})
    return {
        "id": str(updated["_id"]),
        "name": updated.get("name"),
        "email": updated.get("email"),
        "role": updated.get("role", "user"),
        "account_status": updated.get("account_status", "active"),
    }


async def update_admin_user_status(
    target_user_id: str,
    account_status: str,
    current_user: dict,
) -> dict:
    normalized_status = (account_status or "").strip().lower()
    if normalized_status not in ALLOWED_ACCOUNT_STATUSES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Status must be one of: {', '.join(sorted(ALLOWED_ACCOUNT_STATUSES))}",
        )

    if target_user_id == current_user.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own account status from admin panel.",
        )

    db = get_database()
    try:
        target_oid = ObjectId(target_user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID format.",
        )

    target_user = await db["users"].find_one({"_id": target_oid})
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found.",
        )

    await db["users"].update_one(
        {"_id": target_oid},
        {"$set": {"account_status": normalized_status, "updated_at": datetime.now(UTC)}},
    )

    await _insert_audit_log(
        actor_user=current_user,
        action="user.status_updated",
        target_user_id=target_user_id,
        details={
            "old_status": target_user.get("account_status", "active"),
            "new_status": normalized_status,
            "target_email": target_user.get("email"),
        },
    )

    updated = await db["users"].find_one({"_id": target_oid})
    return {
        "id": str(updated["_id"]),
        "name": updated.get("name"),
        "email": updated.get("email"),
        "role": updated.get("role", "user"),
        "account_status": updated.get("account_status", "active"),
    }


async def get_admin_audit_logs(limit: int = 25) -> dict:
    db = get_database()
    safe_limit = min(max(limit, 1), 100)

    logs = await db["audit_logs"].find({}).sort("created_at", -1).limit(safe_limit).to_list(length=safe_limit)
    items = []
    for log in logs:
        details = log.get("details") or {}
        action = log.get("action", "unknown.action")
        actor = log.get("actor_email") or "system"
        target = details.get("target_email") or log.get("target_user_id")
        summary = action
        if action == "user.role_updated":
            summary = f"Role changed to {details.get('new_role')}"
        elif action == "user.status_updated":
            summary = f"Status changed to {details.get('new_status')}"

        items.append({
            "id": str(log["_id"]),
            "action": summary,
            "raw_action": action,
            "actor": actor,
            "target": target,
            "timestamp": log.get("created_at"),
        })

    return {
        "total": len(items),
        "logs": items,
    }
