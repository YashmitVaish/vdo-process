import { useState, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Film } from "lucide-react";
import VideoUploader from "../components/VideoUploader";
import VideoCard, { type VideoFile } from "../components/VideoCard";
import ProcessingOptions from "../components/ProcessingOptions";
import MergeControls from "../components/MergeControls";

const Index = () => {
  const [videos, setVideos] = useState<VideoFile[]>([]);

  const handleUpload = useCallback(async (files: File[]) => {
    for (const file of files) {
      try {
        // 1️⃣ Get presigned upload URL
        const uploadRes = await fetch("http://localhost:8000/assets/upload-url", {
          method: "POST",
        });

        if (!uploadRes.ok) throw new Error("Failed to get upload URL");

        const { upload_url, asset_id } = await uploadRes.json();

        // 2️⃣ Upload video to MinIO
        const putRes = await fetch(upload_url, {
          method: "PUT",
          headers: {
            "Content-Type": file.type || "video/mp4",
          },
          body: file,
        });

        if (!putRes.ok) throw new Error("Upload failed");

        // 3️⃣ Create analyze job
        const jobRes = await fetch("http://localhost:8000/create-job", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            asset_ids: [asset_id],
            job_type: "analyze",
          }),
        });

        if (!jobRes.ok) throw new Error("Failed to create analyze job");

        const { job_id } = await jobRes.json();

        // 4️⃣ Poll job status
        let status = "processing";

        while (status !== "completed") {
          await new Promise((r) => setTimeout(r, 2000));

          const statusRes = await fetch(
            `http://localhost:8000/get-job-status/${job_id}`,
            { method: "POST" }
          );

          const statusData = await statusRes.json();
          status = statusData.status;

          if (status === "failed") {
            throw new Error("Analysis failed");
          }
        }

        // 5️⃣ Fetch metadata
        const metaRes = await fetch(
          `http://localhost:8000/get-analysis/${job_id}`
        );

        const metadata = await metaRes.json();

        const videoStream = metadata.streams.find(
          (s: any) => s.codec_type === "video"
        );

        const format = metadata.format;

        const width = videoStream.width;
        const height = videoStream.height;

        // FPS calculation
        const fpsParts = videoStream.r_frame_rate.split("/");
        const fps =
          Number(fpsParts[1]) !== 0
            ? Math.round(Number(fpsParts[0]) / Number(fpsParts[1]))
            : 0;

        // Proper ratio formatter (16:9 instead of decimal)
        const getAspectRatio = (w: number, h: number): string => {
          const gcd = (a: number, b: number): number =>
            b === 0 ? a : gcd(b, a % b);
          const divisor = gcd(w, h);
          return `${w / divisor}:${h / divisor}`;
        };

        const aspect =
          videoStream.display_aspect_ratio &&
          videoStream.display_aspect_ratio !== "0:1"
            ? videoStream.display_aspect_ratio
            : getAspectRatio(width, height);

        const newVideo: VideoFile = {
          id: asset_id,
          name: file.name,
          size: file.size,
          file,
          url: URL.createObjectURL(file),
          resolution: `${width}×${height}`,
          frameRate: `${fps} fps`,
          duration: `${Math.floor(Number(format.duration))}s`,
          aspectRatio: aspect,
        };

        setVideos((prev) => [...prev, newVideo]);
      } catch (err) {
        console.error("Upload/Analysis error:", err);
      }
    }
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

        <ProcessingOptions videosCount={videos.length} />
        <MergeControls videos={videos} />
      </main>
    </div>
  );
};

export default Index;