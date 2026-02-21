import time
from redis_client import redis_client, JOB_QUEUE
from job import jobs, JobStatus, JobType
from ffmpeg.utils.ffmpeg import a

print("Worker started...")

while True:
    job_id = redis_client.brpop(JOB_QUEUE, timeout=5)

    if not job_id:
        continue

    job_id = job_id[1]
    job = jobs.get(job_id)
    print(job)

    if not job:
        continue

    try:
        job["status"] = JobStatus.processing

        if job["job_type"] == JobType.analyze:
            


        job["status"] = JobStatus.completed
        job["progress"] = 100

    except Exception as e:
        job["status"] = JobStatus.failed
        job["error"] = str(e)