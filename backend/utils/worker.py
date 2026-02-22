import json
from backend.utils.redis_client import redis_client, JOB_QUEUE
from backend.utils.job import JobStatus, JobType
from ffmpeg.utils.ffmpeg import get_metadata,process_video,merge_videos_with_crossfade
from backend.utils.minio import s3, BUCKET_NAME

from pathlib import Path

TEMP_DIR = Path("tmp")
TEMP_DIR.mkdir(exist_ok=True)


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

        if job_type == JobType.normalize.value:
            asset_id = asset_ids[0]
            key = f"raw/{asset_id}.mp4"
            output_key = f"normalized/{asset_id}.mp4"

            redis_client.hset(job_key, mapping={
                "step": "normalize",
                "progress": 20,
                "status": JobStatus.processing.value,
            })

            # generate signed URLs
            input_url = s3.generate_presigned_url(
                "get_object",
                Params={"Bucket": BUCKET_NAME, "Key": key},
                ExpiresIn=3600,
            )

            output_path = TEMP_DIR / f"{asset_id}_normalized.mp4"

            # normalize video
            success = process_video(input_url, str(output_path))

            if not success:
                raise RuntimeError("Video normalization failed")

            redis_client.hset(job_key, mapping={"progress": 70})

            # upload to minio
            s3.upload_file(output_path, BUCKET_NAME, output_key)

            redis_client.hset(job_key, mapping={
                "outputs": json.dumps({"normalized_key": output_key}),
                "progress": 100,
                "status": JobStatus.completed.value,
                "step": "complete",
            })
        
        if job_type == JobType.merge.value:
            redis_client.hset(job_key, mapping={
                "step": "merge",
                "progress": 20,
                "status": JobStatus.processing.value,
            })

            if len(asset_ids) < 2:
                redis_client.hset(job_key, mapping={
                    "status": JobStatus.failed.value,
                    "step": "not enough files",
                    "progress": 100,
                })
                continue

            asset_1, asset_2 = asset_ids[:2]

            local_1 = TEMP_DIR / f"{asset_1}.mp4"
            local_2 = TEMP_DIR / f"{asset_2}.mp4"
            output_path = TEMP_DIR / f"{asset_1}_{asset_2}_merged.mp4"

            # download inputs
            s3.download_file(BUCKET_NAME, f"raw/{asset_1}.mp4", str(local_1))
            s3.download_file(BUCKET_NAME, f"raw/{asset_2}.mp4", str(local_2))

            redis_client.hset(job_key, mapping={"progress": 40})

            # get duration for xfade offset
            metadata = get_metadata(str(local_1))
            duration = float(metadata["format"]["duration"])

            success = merge_videos_with_crossfade(
                str(local_1),
                str(local_2),
                str(output_path),
                fade_duration=2,
                offset=duration - 2
            )

            if not success:
                raise RuntimeError("Merge failed")

            redis_client.hset(job_key, mapping={"progress": 80})

            output_key = f"merged/{asset_1}_{asset_2}.mp4"
            s3.upload_file(str(output_path), BUCKET_NAME, output_key)

            redis_client.hset(job_key, mapping={
                "outputs": json.dumps({"merged_key": output_key}),
                "status": JobStatus.completed.value,
                "progress": 100,
                "step": None,
            })
            
        redis_client.hset(job_key, mapping={
            "status": JobStatus.completed.value,
            "progress": 100,
            "step": "",
        })

    except Exception as e:
        print(e)
        redis_client.hset(job_key, mapping={
            "status": JobStatus.failed.value,
            "error": str(e),
        })