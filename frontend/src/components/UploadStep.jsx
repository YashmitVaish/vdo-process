import React from "react";
import { uploadVideo } from "../api";

export default function UploadStep({ videos, setVideos, setStep }) {

  const handleUpload = async (files) => {
    const fileArray = Array.from(files);

    for (let file of fileArray) {
      const response = await uploadVideo(file);

      setVideos(prev => [
        ...prev,
        {
          file_id: response.file_id,
          signed_url: response.signed_url,
          name: file.name
        }
      ]);
    }
  };

  return (
    <div className="panel">
      <h2>Upload Videos</h2>

      <div
  className="drop-zone"
  onDragOver={(e) => e.preventDefault()}
  onDrop={(e) => handleUpload(e.dataTransfer.files)}
>

  {/* Upload Logo */}
  <svg
    width="70"
    height="70"
    viewBox="0 0 24 24"
    style={{ marginBottom: "10px" }}
  >
    <path
      d="M12 16V4M12 4l-4 4M12 4l4 4M4 20h16"
      stroke="#c9a227"
      strokeWidth="1.5"
      fill="none"
    />
  </svg>

  <input
    type="file"
    multiple
    accept="video/*"
    onChange={(e) => handleUpload(e.target.files)}
  />  
</div>

      {videos.length > 0 && (
        <>
          <h3 style={{ marginTop: "30px" }}>Uploaded Clips</h3>

          <div className="video-grid">
            {videos.map((video, i) => (
              <div key={i} className="video-card">
                <video
                  src={video.signed_url}
                  controls
                  style={{ width: "100%" }}
                />
                <p>{video.name}</p>
              </div>
            ))}
          </div>

          <button
            className="primary-btn"
            onClick={() => setStep("resolution")}
          >
            Enhance
          </button>
        </>
      )}
    </div>
  );
}