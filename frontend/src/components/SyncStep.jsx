import React from "react";
import { convertVideos } from "../api";

export default function SyncStep({ videos, resolution, normalize }) {

  const handleSync = async () => {
    await convertVideos({
      file_ids: videos.map(v => v.file_id),
      resolution,
      normalize_audio: normalize
    });

    alert("Synchronization Started");
  };

  return (
    <div className="panel">
      <h2>Synchronize</h2>

      <button className="primary-btn" onClick={handleSync}>
        Start Synchronization
      </button>
    </div>
  );
}