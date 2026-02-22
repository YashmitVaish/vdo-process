from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from uuid import uuid4
from backend.utils.minio import BUCKET_NAME,s3
from backend.utils.redis_client import redis_client,JOB_QUEUE
from backend.utils.job import create_job,JobType
from backend.utils.mongo import assets_col
from backend.utils.stream_manager import start_stream,get_stream_status,stop_stream,list_active_streams
from datetime import datetime , timezone
import json

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

    assets_col.insert_one({
        "_id": asset_id,
        "raw_key": object_key,
        "normalized_key": None,
        "status": "uploaded",
        "created_at": datetime.now(timezone.utc),
    })

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

@app.get("/get-analysis/{job_id}")
async def get_job_analytics(job_id: str):
    job = redis_client.hgetall(f"job:{job_id}")

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    def decode(x):
        return x.decode() if isinstance(x, (bytes, bytearray)) else x

    job = {decode(k): decode(v) for k, v in job.items()}

    status = job.get("status")
    progress = int(job.get("progress", 0))

    if status != "completed":
        return {
            "status": status,
            "progress": progress,
            "step": job.get("step"),
        }

    outputs = json.loads(job.get("outputs", "{}"))
    metadata = outputs.get("metadata")

    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata missing")

    return metadata

class StartStreamRequest(BaseModel):
    rtsp_url: str
    stream_id: str | None = None  # optional — auto-generated if not provided


class StartStreamResponse(BaseModel):
    stream_id: str
    rtmp_url: str
    hls_preview: str
    status: str


class StreamStatusResponse(BaseModel):
    stream_id: str
    status: str
    rtsp_url: str
    rtmp_url: str
    hls_preview: str | None = None
    reconnect_attempt: int | None = None

@app.post("/streams/start", response_model=StartStreamResponse)
async def api_start_stream(req: StartStreamRequest):
    """
    Start a live RTSP → normalize → RTMP stream.

    The RTSP URL is the camera source (e.g. rtsp://192.168.1.50/stream1).
    The normalized stream will be published to MediaMTX at:
        rtmp://localhost:1935/live/{stream_id}

    You can also view it in a browser via HLS at:
        http://localhost:8888/{stream_id}/index.m3u8
    """
    try:
        result = start_stream(req.rtsp_url, stream_id=req.stream_id)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return result


@app.post("/streams/{stream_id}/stop")
async def api_stop_stream(stream_id: str):
    """
    Stop a running stream.
    """
    try:
        result = stop_stream(stream_id)
    except RuntimeError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return result


@app.get("/streams/{stream_id}/status", response_model=StreamStatusResponse)
async def api_stream_status(stream_id: str):
    """
    Get current status of a stream from Redis.
    """
    data = get_stream_status(stream_id)
    if not data:
        raise HTTPException(status_code=404, detail="Stream not found")

    return {
        "stream_id": stream_id,
        "status": data.get("status", "unknown"),
        "rtsp_url": data.get("rtsp_url", ""),
        "rtmp_url": data.get("rtmp_url", ""),
        "hls_preview": f"http://localhost:8888/{stream_id}/index.m3u8",
        "reconnect_attempt": int(data.get("reconnect_attempt", 0)),
    }


@app.get("/streams")
async def api_list_streams():
    """
    List all currently active stream IDs.
    """
    return {"active_streams": list_active_streams()}