from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4
from utils.minio import BUCKET_NAME,s3

app = FastAPI(title="Video Backend")


class UploadURLResponse(BaseModel):
    asset_id: str
    upload_url: str

@app.post("/assets/upload-url", response_model=UploadURLResponse)
def get_upload_url():
    asset_id = str(uuid4())
    object_key = f"raw/{asset_id}.mp4"

    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": object_key,
            "ContentType": "video/mp4",
        },
        ExpiresIn=3600,
    )

    return {
        "asset_id": asset_id,
        "upload_url": upload_url,
    }

@app.get("/assets/{asset_id}/stream")
def stream_video(asset_id: str):
    key = f"raw/{asset_id}.mp4"

    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": key,
        },
        ExpiresIn=3600,
    )

    return {"stream_url": url}