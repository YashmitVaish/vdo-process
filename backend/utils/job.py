from enum import Enum
from uuid import uuid4
from typing import Dict

class JobStatus(str, Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"

jobs: Dict[str, dict] = {}

def create_job(asset_id: str) -> dict:
    job_id = str(uuid4())
    job = {
        "job_id": job_id,
        "asset_id": asset_id,
        "status": JobStatus.queued,
        "progress": 0,
        "error": None,
    }
    jobs[job_id] = job
    return job