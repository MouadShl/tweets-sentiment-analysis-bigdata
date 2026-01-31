import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
print("MONGO_URI =", uri)

client = MongoClient(uri, serverSelectionTimeoutMS=5000)
print(client.admin.command("ping"))
print("✅ Mongo connection OK")
