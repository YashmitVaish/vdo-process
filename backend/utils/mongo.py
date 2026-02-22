from pymongo import MongoClient
from dotenv import load_dotenv
import os
import certifi

load_dotenv()

client = MongoClient(
    os.getenv("MONGO_URI"),
    tlsCAFile=certifi.where()
)

db = client["video_backend"]
assets_col = db["assets"]
jobs_col = db["jobs"]
streams_col = db["streams"]