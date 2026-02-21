import json
from backend.utils.redis_client import redis_client, JOB_QUEUE
from backend.utils.job import JobStatus, JobType
from ffmpeg.utils.ffmpeg import get_metadata
from backend.utils.minio import s3, BUCKET_NAME

print("Worker started...")

while True:
    item = redis_client.brpop(JOB_QUEUE, timeout=5)
    print(item)
    if not item:
        continue

    job_id = item[1]
    job_key = f"job:{job_id}"
    job = redis_client.hgetall(job_key)

    if not job:
        continue

    try:
        redis_client.hset(job_key, mapping={"status": JobStatus.processing.value})

        job_type = job["job_type"]
        asset_ids = json.loads(job["asset_ids"])

        if job_type == JobType.analyze.value:
            asset_id = asset_ids[0]
            key = f"raw/{asset_id}.mp4"

            redis_client.hset(job_key, mapping={"step": "analysis", "progress": 20})

            input_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
            )

            metadata = get_metadata(input_url)
            redis_client.hset(job_key, mapping={
                "outputs": json.dumps({"metadata": metadata})
            })

        redis_client.hset(job_key, mapping={
            "status": JobStatus.completed.value,
            "progress": 100,
            "step": "",
        })

    except Exception as e:
        redis_client.hset(job_key, mapping={
            "status": JobStatus.failed.value,
            "error": str(e),
        })