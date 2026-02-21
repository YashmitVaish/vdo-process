import React from "react";
import Card from "./Card";
import { uploadVideos } from "../api";

export default function UploadPanel({ videos, setVideos, setJobId }) {
  const handleFiles = async (files) => {
    const fileArray = Array.from(files);
    setVideos(fileArray);
    const response = await uploadVideos(fileArray);
    setJobId(response.job_id);
  };

  return (
    <Card>
      <h2>Upload Videos</h2>
      <input
        type="file"
        multiple
        accept="video/*"
        onChange={(e) => handleFiles(e.target.files)}
      />

      <div className="video-grid">
        {videos.map((file, i) => (
          <video
            key={i}
            src={URL.createObjectURL(file)}
            height="120"
            controls
          />
        ))}
      </div>
    </Card>
  );
}