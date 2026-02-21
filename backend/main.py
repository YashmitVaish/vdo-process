from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from backend.utils.minio import BUCKET_NAME,s3
from backend.utils.redis_client import redis_client,JOB_QUEUE
from backend.utils.job import create_job,jobs,JobType

app = FastAPI(title="Video Backend")
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

class UploadURLResponse(BaseModel):
    asset_id: str
    upload_url: str

class CreateJobRequest(BaseModel):
    asset_ids: list[str]
    job_type: JobType

class JobResponse(BaseModel):
    job_id: str
    status: str

class GetJobResponse(BaseModel):
    status : str

@app.post("/assets/upload-url", response_model=UploadURLResponse)
async def get_upload_url():
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
async def stream_video(asset_id: str):
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

@app.post("/create-job", response_model=JobResponse)
async def create_processing_job(req: CreateJobRequest):
    job = create_job(req.asset_ids,job_type=req.job_type)

    redis_client.lpush(JOB_QUEUE, job["job_id"])

    return {
        "job_id": job["job_id"],
        "status": job["status"],
    }

@app.post("/get-job-status/{job_id}",response_model=GetJobResponse)
async def get_job_status(job_id : str):
    job = redis_client.hgetall(f"job:{job_id}")
    if not job:
        return {"status":"no job found (unknown)"}
    return {
        "status": job["status"]
    }

@app.post("get-analysis/{job_id}")
async def get_job_analytics(job_id : str)
    