import React, { useState } from "react";

import Header from "./components/Header";
import StepNavigation from "./components/StepNavigation";
import UploadStep from "./components/UploadStep";
import ResolutionStep from "./components/ResolutionStep";
import AudioStep from "./components/AudioStep";
import SyncStep from "./components/SyncStep";

export default function App() {

  const [step, setStep] = useState("upload");

  const [videos, setVideos] = useState([]);
  const [resolution, setResolution] = useState("1080p");
  const [fps, setFps] = useState("30fps");
  const [aspect, setAspect] = useState("16:9");
  const [normalize, setNormalize] = useState(true);

  return (
    <div className="container">

      <Header />

      <StepNavigation step={step} setStep={setStep} />

      {step === "upload" && (
        <UploadStep
          videos={videos}
          setVideos={setVideos}
          setStep={setStep}
        />
      )}

      {step === "resolution" && (
        <ResolutionStep
          resolution={resolution}
          setResolution={setResolution}
          fps={fps}
          setFps={setFps}
          aspect={aspect}
          setAspect={setAspect}
          setStep={setStep}
        />
      )}

      {step === "audio" && (
        <AudioStep
          normalize={normalize}
          setNormalize={setNormalize}
          setStep={setStep}
        />
      )}

      {step === "sync" && (
        <SyncStep
          videos={videos}
          resolution={resolution}
          fps={fps}
          aspect={aspect}
          normalize={normalize}
        />
      )}

    </div>
  );
}