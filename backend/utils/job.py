from enum import Enum
from uuid import uuid4
from typing import Dict
import json
from backend.utils.redis_client import redis_client
from backend.utils.mongo import jobs_col
from datetime import datetime, timezone

class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class JobType(str, Enum):
    normalize = "normalize"
    analyze = "analyze"
    merge = "merge"
    livestream = "livestream" 

def create_job(asset_ids: list[str], job_type: JobType, params: dict | None = None) -> dict:
    job_id = str(uuid4())
    now = datetime.now(timezone.utc)

    job = {
        "job_id": job_id,
        "job_type": job_type.value,
        "asset_ids": asset_ids,
        "status": JobStatus.queued.value,
        "step": None,
        "progress": 0,
        "outputs": {},
        "error": None,
        "created_at": now,
        "updated_at": now,
    }

    redis_client.hset(f"job:{job_id}", mapping={
        "job_id": job_id,
        "job_type": job_type.value,
        "asset_ids": json.dumps(asset_ids),
        "status": JobStatus.queued.value,
        "progress": 0,
    })

    jobs_col.insert_one({**job, "_id": job_id})
    return job