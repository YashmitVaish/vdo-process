import React from "react";

export default function StepNavigation({ step, setStep }) {
  const steps = ["upload", "resolution", "audio", "sync"];

  return (
    <div className="step-nav">
      {steps.map((s) => (
        <div
          key={s}
          className={`step-card ${step === s ? "active" : ""}`}
          onClick={() => setStep(s)}
        >
          <h3 style={{ textTransform: "capitalize" }}>{s}</h3>
        </div>
      ))}
    </div>
  );
}