import React from "react";
import Card from "./Card";
import { processVideos } from "../api";

export default function ProcessPanel({ jobId, resolution, normalizeAudio, offsets, progress, setProgress }) {

  const handleProcess = async () => {
    if (!jobId) return alert("Upload videos first");

    setProgress(30);

    await processVideos({
      job_id: jobId,
      resolution,
      normalize_audio: normalizeAudio,
      sync_offsets: offsets,
    });

    setProgress(100);
    alert("Processing Complete");
  };

  return (
    <Card>
      <h2>Process Media</h2>

      <button onClick={handleProcess}>Start Processing</button>

      {progress > 0 && (
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      )}
    </Card>
  );
}