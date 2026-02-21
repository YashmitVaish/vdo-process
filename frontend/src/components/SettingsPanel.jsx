import React from "react";
import Card from "./Card";

export default function SettingsPanel({ resolution, setResolution, normalizeAudio, setNormalizeAudio }) {
  return (
    <Card>
      <h2>Output Settings</h2>

      <div>
        <label>Resolution:</label>
        <select value={resolution} onChange={(e) => setResolution(e.target.value)}>
          <option value="1280x720">720p</option>
          <option value="1920x1080">1080p</option>
          <option value="3840x2160">4K</option>
        </select>
      </div>

      <div style={{ marginTop: "15px" }}>
        <label>
          <input
            type="checkbox"
            checked={normalizeAudio}
            onChange={(e) => setNormalizeAudio(e.target.checked)}
          />
          Normalize Audio (-16 LUFS)
        </label>
      </div>
    </Card>
  );
}