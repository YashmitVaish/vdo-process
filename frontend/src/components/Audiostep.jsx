import React from "react";

export default function AudioStep({ normalize, setNormalize }) {
  return (
    <div className="panel">
      <h2>Audio Enhancement</h2>

      <label>
        <input
          type="checkbox"
          checked={normalize}
          onChange={(e) => setNormalize(e.target.checked)}
        />
        Normalize Audio Levels
      </label>
    </div>
  );
}