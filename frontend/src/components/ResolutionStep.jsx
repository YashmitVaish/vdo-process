import React from "react";

export default function ResolutionStep({ resolution, setResolution }) {
  const options = ["720p", "1080p", "4K"];

  return (
    <div className="panel">
      <h2>Video Resolution</h2>

      <div className="option-grid">
        {options.map(opt => (
          <div
            key={opt}
            className={`option-card ${resolution === opt ? "selected" : ""}`}
            onClick={() => setResolution(opt)}
          >
            {opt}
          </div>
        ))}
      </div>
    </div>
  );
}