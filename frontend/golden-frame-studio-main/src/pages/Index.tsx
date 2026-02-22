import { useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Film } from "lucide-react";
import VideoUploader from "../components/VideoUploader.tsx";
import VideoCard, { type VideoFile } from "../components/VideoCard";
import ProcessingOptions from "../components/ProcessingOptions";
import MergeControls from "../components/MergeControls";

// Mock metadata generator
const generateMockMeta = (): Pick<VideoFile, "resolution" | "frameRate" | "duration" | "aspectRatio"> => {
  const resolutions = ["1920×1080", "1280×720", "3840×2160", "2560×1440"];
  const fps = ["24 fps", "30 fps", "60 fps"];
  const ratios = ["16:9", "4:3", "21:9"];
  const durations = ["0:32", "1:15", "2:47", "0:58", "3:22", "5:01"];
  const pick = <T,>(arr: T[]) => arr[Math.floor(Math.random() * arr.length)];
  return {
    resolution: pick(resolutions),
    frameRate: pick(fps),
    duration: pick(durations),
    aspectRatio: pick(ratios),
  };
};

const Index = () => {
  const [videos, setVideos] = useState<VideoFile[]>([]);

  const handleUpload = useCallback(async (files: File[]) => {
  const uploadedVideos: VideoFile[] = [];

  for (const file of files) {
    try {
      // 1️⃣ Ask backend for presigned URL
      const res = await fetch("http://localhost:8000/assets/upload-url", {
        method: "POST",
      });

      if (!res.ok) {
        throw new Error("Failed to get upload URL");
      }

      const { upload_url, asset_id } = await res.json();

      // 2️⃣ Upload file directly to MinIO
      const uploadRes = await fetch(upload_url, {
        method: "PUT",
        headers: {
          "Content-Type": file.type || "video/mp4",
        },
        body: file,
      });

      if (!uploadRes.ok) {
        throw new Error("Upload failed");
      }

      console.log("Uploaded asset:", asset_id);

      // 3️⃣ Add to UI (replace random id with real asset_id)
      uploadedVideos.push({
        id: asset_id,
        name: file.name,
        size: file.size,
        file,
        url: URL.createObjectURL(file),
        ...generateMockMeta(),
      });

    } catch (error) {
      console.error("Upload error:", error);
    }
  }

  setVideos((prev) => [...prev, ...uploadedVideos]);
}, []);

  const handleRemove = useCallback((id: string) => {
    setVideos((prev) => {
      const v = prev.find((v) => v.id === id);
      if (v) URL.revokeObjectURL(v.url);
      return prev.filter((v) => v.id !== id);
    });
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border">
        <div className="container mx-auto flex items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="rounded-lg bg-primary/10 p-2">
              <Film className="h-5 w-5 text-primary" />
            </div>
            <h1 className="text-xl font-bold">
              <span className="gold-text-gradient">FrameForge</span>
            </h1>
          </div>
          <span className="font-mono text-xs text-muted-foreground">
            {videos.length} video{videos.length !== 1 && "s"} loaded
          </span>
        </div>
      </header>

      <main className="container mx-auto space-y-8 px-6 py-8">
        {/* Upload */}
        <VideoUploader onUpload={handleUpload} />

        {/* Video Collection */}
        {videos.length > 0 && (
          <motion.section
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-4"
          >
            <h2 className="text-lg font-semibold text-foreground">
              Video Collection
            </h2>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              <AnimatePresence mode="popLayout">
                {videos.map((video, i) => (
                  <VideoCard
                    key={video.id}
                    video={video}
                    onRemove={handleRemove}
                    index={i}
                  />
                ))}
              </AnimatePresence>
            </div>
          </motion.section>
        )}

        {/* Processing Options */}
        <ProcessingOptions videosCount={videos.length} />

        {/* Merge & Sync */}
        <MergeControls videos={videos} />
      </main>
    </div>
  );
};

export default Index;
