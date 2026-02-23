# 🎥 VDO-Process — Media Processing & Normalization MVP

A hackathon MVP for **uploading, processing, normalizing, merging, and streaming large video files** using an async, scalable backend architecture.

This project demonstrates how heterogeneous video assets (different resolutions, FPS, audio levels, sources) can be **analyzed, normalized, merged, and streamed** through a unified API.

---

## 🚀 What This Project Does

- Upload **large video files** safely (no backend memory usage)
- Analyze video/audio metadata (FFprobe)
- Normalize video & audio to a target profile
- Merge multiple videos (with transitions)
- Track processing jobs asynchronously
- Stream processed videos directly to the frontend

All processing is done **asynchronously** using a job queue and background workers.

---

## 🧠 Key Features

- **Large-file safe uploads** using signed URLs  
- **Async job processing** with Redis queue  
- **Video normalization** (resolution, FPS, audio loudness)  
- **Video merging** (crossfade support)  
- **Streamable outputs** via object storage  
- **Hackathon-ready MVP architecture**

---

## 🏗️ Architecture Overview

```
Frontend (React)
   ↓
FastAPI Backend
   ├── Signed upload URLs
   ├── Job orchestration
   ├── Job status APIs
   ↓
Redis (Job Queue)
   ↓
Worker Process
   ├── FFprobe (analysis)
   ├── FFmpeg (normalize / merge)
   ↓
MinIO (Object Storage)
   ├── raw videos
   ├── processed videos
   └── previews
```

---

## 🛠 Tech Stack

### Backend
- FastAPI
- Python
- FFmpeg / FFprobe
- Redis (job broker)
- MinIO (S3-compatible object storage)

### Frontend
- React

### Infrastructure
- Docker & Docker Compose

---

## ▶️ How to Run Locally

### 1️⃣ Start infrastructure
```bash
docker compose up -d
```

Create a bucket in MinIO named:
```
media
```

---

### 2️⃣ Start backend
```bash
cd backend
uvicorn main:app --reload
```

API docs:
```
http://localhost:8000/docs
```

---

### 3️⃣ Start worker
```bash
python worker.py
```

---

## 📡 Example API Endpoints

- `POST /assets/upload-url` → get signed upload URL  
- `POST /create-job` → create processing job  
- `GET /get-job-status/{job_id}` → job progress  
- `GET /stream/{asset_id}` → stream video  

---

## ⚠️ MVP Notes

This is a **hackathon MVP**, not a production system.

- In-memory job state
- Single worker
- No auth
- No retries or persistence guarantees

---

## 🎯 Why This Matters

This project demonstrates:
- Practical handling of large media files
- Async processing pipelines
- Real-world media tooling (FFmpeg)

---
