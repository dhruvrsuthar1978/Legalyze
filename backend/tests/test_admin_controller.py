import re
import asyncio

import pytest
from bson import ObjectId
from fastapi import HTTPException

from app.controllers import admin_controller


class FakeCursor:
    def __init__(self, docs):
        self.docs = list(docs)

    def sort(self, field, order):
        reverse = order == -1
        self.docs.sort(key=lambda d: d.get(field), reverse=reverse)
        return self

    def skip(self, value):
        self.docs = self.docs[value:]
        return self

    def limit(self, value):
        self.docs = self.docs[:value]
        return self

    async def to_list(self, length=None):
        if length is None:
            return self.docs
        return self.docs[:length]


class FakeAggregateCursor:
    def __init__(self, docs):
        self.docs = docs

    async def to_list(self, length=None):
        if length is None:
            return self.docs
        return self.docs[:length]


class FakeUsersCollection:
    def __init__(self, docs):
        self.docs = docs

    async def count_documents(self, query):
        return len(self._apply_filter(query))

    def find(self, query):
        return FakeCursor(self._apply_filter(query))

    async def find_one(self, query):
        for doc in self.docs:
            if doc.get("_id") == query.get("_id"):
                return doc
        return None

    async def update_one(self, query, update):
        target = await self.find_one(query)
        if not target:
            return
        for key, value in (update.get("$set") or {}).items():
            target[key] = value

    def _apply_filter(self, query):
        if not query:
            return list(self.docs)
        if "$or" in query:
            filtered = []
            for doc in self.docs:
                for condition in query["$or"]:
                    field, cfg = next(iter(condition.items()))
                    pattern = cfg.get("$regex", "")
                    if re.search(pattern, str(doc.get(field, "")), re.IGNORECASE):
                        filtered.append(doc)
                        break
            return filtered
        return list(self.docs)


class FakeContractsCollection:
    def __init__(self, docs):
        self.docs = docs

    def aggregate(self, pipeline):
        user_ids = pipeline[0]["$match"]["user_id"]["$in"]
        counts = {}
        for doc in self.docs:
            uid = doc.get("user_id")
            if uid in user_ids:
                counts[uid] = counts.get(uid, 0) + 1
        grouped = [{"_id": uid, "count": count} for uid, count in counts.items()]
        return FakeAggregateCursor(grouped)


class FakeAuditCollection:
    def __init__(self, docs=None):
        self.docs = docs or []

    async def insert_one(self, payload):
        payload = dict(payload)
        payload["_id"] = ObjectId()
        self.docs.append(payload)

    def find(self, _query):
        return FakeCursor(self.docs)


class FakeDB:
    def __init__(self, users=None, contracts=None, audit_logs=None):
        self.collections = {
            "users": FakeUsersCollection(users or []),
            "contracts": FakeContractsCollection(contracts or []),
            "audit_logs": FakeAuditCollection(audit_logs or []),
        }

    def __getitem__(self, key):
        return self.collections[key]


def test_get_admin_users_returns_paginated_users_with_contract_counts(monkeypatch):
    user_a = {"_id": ObjectId(), "name": "Alice", "email": "alice@example.com", "role": "admin", "account_status": "active"}
    user_b = {"_id": ObjectId(), "name": "Bob", "email": "bob@example.com", "role": "user", "account_status": "active"}
    fake_db = FakeDB(
        users=[user_a, user_b],
        contracts=[
            {"user_id": str(user_a["_id"])},
            {"user_id": str(user_a["_id"])},
            {"user_id": str(user_b["_id"])},
        ],
    )
    monkeypatch.setattr(admin_controller, "get_database", lambda: fake_db)

    result = asyncio.run(admin_controller.get_admin_users(page=1, limit=10, query="ali"))

    assert result["total"] == 1
    assert len(result["users"]) == 1
    assert result["users"][0]["email"] == "alice@example.com"
    assert result["users"][0]["contracts"] == 2


def test_update_admin_user_role_updates_user_and_writes_audit_log(monkeypatch):
    target_id = ObjectId()
    fake_db = FakeDB(
        users=[{"_id": target_id, "name": "User One", "email": "u1@example.com", "role": "user", "account_status": "active"}]
    )
    monkeypatch.setattr(admin_controller, "get_database", lambda: fake_db)

    current_user = {"sub": str(ObjectId()), "email": "admin@example.com"}
    updated = asyncio.run(admin_controller.update_admin_user_role(str(target_id), "admin", current_user))

    assert updated["role"] == "admin"
    assert len(fake_db["audit_logs"].docs) == 1
    assert fake_db["audit_logs"].docs[0]["action"] == "user.role_updated"


def test_update_admin_user_status_blocks_self_update(monkeypatch):
    current_id = ObjectId()
    fake_db = FakeDB(users=[{"_id": current_id, "name": "Self Admin", "email": "self@example.com", "role": "admin", "account_status": "active"}])
    monkeypatch.setattr(admin_controller, "get_database", lambda: fake_db)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(
            admin_controller.update_admin_user_status(
                str(current_id),
                "suspended",
                {"sub": str(current_id), "email": "self@example.com"},
            )
        )

    assert exc.value.status_code == 400


def test_get_admin_audit_logs_formats_summary(monkeypatch):
    fake_db = FakeDB(
        audit_logs=[
            {
                "_id": ObjectId(),
                "action": "user.status_updated",
                "actor_email": "admin@example.com",
                "target_user_id": "u1",
                "details": {"new_status": "suspended", "target_email": "u1@example.com"},
                "created_at": "2026-01-01T10:00:00",
            }
        ]
    )
    monkeypatch.setattr(admin_controller, "get_database", lambda: fake_db)

    result = asyncio.run(admin_controller.get_admin_audit_logs(limit=10))

    assert result["total"] == 1
    assert result["logs"][0]["action"] == "Status changed to suspended"
    assert result["logs"][0]["actor"] == "admin@example.com"
