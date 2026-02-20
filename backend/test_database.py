# test_database.py

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings

async def test_db():
    print("🧪 Testing MongoDB connection...\n")
    
    try:
        # Connect
        client = AsyncIOMotorClient(settings.MONGODB_URI)
        db = client[settings.DB_NAME]
        
        # Ping
        await client.admin.command("ping")
        print("✅ MongoDB connection successful")
        
        # Test write
        test_collection = db["test"]
        result = await test_collection.insert_one({"test": "value"})
        print(f"✅ Write test successful (ID: {result.inserted_id})")
        
        # Test read
        doc = await test_collection.find_one({"_id": result.inserted_id})
        print(f"✅ Read test successful (Data: {doc})")
        
        # Cleanup
        await test_collection.delete_one({"_id": result.inserted_id})
        print("✅ Cleanup successful")
        
        # Close
        client.close()
        print("\n✅ All database tests passed!")
        
    except Exception as e:
        print(f"\n❌ Database test failed: {e}")
        exit(1)

asyncio.run(test_db())