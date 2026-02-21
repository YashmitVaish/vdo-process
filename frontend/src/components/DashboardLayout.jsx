import React, { useState } from "react";
import "../styles/theme.css";
import Header from "./Header";
import StepNavigation from "./StepNavigation";
import UploadStep from "./UploadStep";
import ResolutionStep from "./ResolutionStep";
import AudioStep from "./AudioStep";
import SyncStep from "./SyncStep";

export default function DashboardLayout() {

  const [step, setStep] = useState("upload");
  const [videos, setVideos] = useState([]);
  const [resolution, setResolution] = useState("1080p");
  const [normalize, setNormalize] = useState(true);

  return (
    <div className="container">
      <Header />
      <StepNavigation step={step} setStep={setStep} />

      {step === "upload" && (
        <UploadStep videos={videos} setVideos={setVideos} />
      )}

      {step === "resolution" && (
        <ResolutionStep
          resolution={resolution}
          setResolution={setResolution}
        />
      )}

      {step === "audio" && (
        <AudioStep
          normalize={normalize}
          setNormalize={setNormalize}
        />
      )}

      {step === "sync" && (
        <SyncStep
          videos={videos}
          resolution={resolution}
          normalize={normalize}
        />
      )}
    </div>
  );
}