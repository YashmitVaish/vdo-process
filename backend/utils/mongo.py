from pymongo import MongoClient
from dotenv import load_dotenv
# import os
# import certifi

load_dotenv()

client = MongoClient(
    "mongodb://admin:password@localhost:27017/?authSource=admin"
)

db = client["video_backend"]
assets_col = db["assets"]
jobs_col = db["jobs"]
streams_col = db["streams"]