# app/config/database.py

from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
import logging

logger = logging.getLogger("legalyze.database")

client = None
_db = None

async def connect_to_mongo():
    """Connect to MongoDB"""
    global client, _db
    try:
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        _db = client[settings.DB_NAME]
        await client.admin.command('ping')
        logger.info(f"[OK] Connected to MongoDB: {settings.DB_NAME}")
    except Exception as e:
        logger.error(f"[ERROR] MongoDB connection failed: {e}")
        raise

async def close_mongo_connection():
    """Close MongoDB connection"""
    global client
    if client:
        client.close()
        logger.info("[OK] MongoDB connection closed")

def get_database():
    """Get database instance"""
    return _db

async def get_db_stats():
    """Get database statistics"""
    try:
        database = get_database()
        stats = await database.command("dbStats")
        return {
            "collections": stats.get("collections", 0),
            "objects": stats.get("objects", 0),
            "dataSize": stats.get("dataSize", 0),
            "storageSize": stats.get("storageSize", 0)
        }
    except:
        return {}