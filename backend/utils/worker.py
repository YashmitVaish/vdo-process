import json
from backend.utils.redis_client import redis_client, JOB_QUEUE
from backend.utils.job import JobStatus, JobType
from ffmpeg.utils.ffmpeg import get_metadata,process_video,merge_videos_with_crossfade
from backend.utils.minio import s3, BUCKET_NAME
from backend.utils.stream_manager import start_stream

from pathlib import Path
from backend.utils.mongo import jobs_col, assets_col
from datetime import datetime, timezone

def update_job_mongo(job_id, fields):
    jobs_col.update_one(
        {"_id": job_id},
        {"$set": {**fields, "updated_at": datetime.now(timezone.utc)}}
    )

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

            update_job_mongo(job_id, {"status": JobStatus.completed.value, "progress": 100, "outputs": {"metadata": metadata}})

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

            update_job_mongo(job_id, {"status": JobStatus.completed.value, "progress": 100, "outputs": {"normalized_key": output_key}})
            assets_col.update_one({"_id": asset_id}, {"$set": {"normalized_key": output_key, "status": "normalized"}})
        
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
                "step": "done",
            })

            update_job_mongo(job_id, {"status": JobStatus.completed.value, "progress": 100, "outputs": {"merged_key": output_key}})
        
        if job_type == JobType.livestream.value:
            # asset_ids[0] is the RTSP URL for livestream jobs
            # (not a MinIO asset — just the camera URL string)
            rtsp_url = asset_ids[0]

            redis_client.hset(job_key, mapping={
                "step": "starting_stream",
                "progress": 10,
                "status": JobStatus.processing.value,
            })

            result = start_stream(rtsp_url)  # non-blocking — returns immediately

            # The job is "complete" in the sense that we successfully started the
            # stream. The stream itself runs indefinitely in stream_manager.
            redis_client.hset(job_key, mapping={
                "outputs": json.dumps({
                    "stream_id": result["stream_id"],
                    "rtmp_url": result["rtmp_url"],
                    "hls_preview": result["hls_preview"],
                }),
                "status": JobStatus.completed.value,
                "progress": 100,
                "step": "streaming",
            })

            update_job_mongo(job_id, {
                "status": JobStatus.completed.value,
                "progress": 100,
                "outputs": {
                    "stream_id": result["stream_id"],
                    "rtmp_url": result["rtmp_url"],
                    "hls_preview": result["hls_preview"],
                },
            })

            # Skip the generic "completed" hset below — already done above
            continue

        redis_client.hset(job_key, mapping={
            "status": JobStatus.completed.value,
            "progress": 100,
            "step": "",
        })

    except Exception as e:
        print(e)
        update_job_mongo(job_id, {"status": JobStatus.failed.value, "progress": 0, "outputs": {"error": str(e)}})

        redis_client.hset(job_key, mapping={
            "status": JobStatus.failed.value,
            "error": str(e),
        })