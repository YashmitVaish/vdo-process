import { motion } from "framer-motion";
import { Merge, Zap } from "lucide-react";
import { useState } from "react";

interface MergeControlsProps {
  videos: { id: string }[];
}

const MergeControls = ({ videos }: MergeControlsProps) => {
  const [jobStatus, setJobStatus] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);

  if (videos.length < 2) return null;

  const createJob = async (type: "merge" | "sync") => {
    try {
      const asset_ids = videos.map((v) => v.id);

      // 1️⃣ Create job
      const res = await fetch("http://localhost:8000/create-job", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          asset_ids,
          job_type: type,
        }),
      });

      const data = await res.json();
      const job_id = data.job_id;

      setJobStatus("processing");

      // 2️⃣ Poll job status
      const interval = setInterval(async () => {
        const statusRes = await fetch(
          `http://localhost:8000/get-job-status/${job_id}`,
          { method: "POST" }
        );

        const statusData = await statusRes.json();

        setJobStatus(statusData.status);

        if (statusData.status === "completed") {
          clearInterval(interval);

          const resultRes = await fetch(
            `http://localhost:8000/get-analysis/${job_id}`
          );

          const result = await resultRes.json();
          console.log("Final result:", result);

          setProgress(100);
        }
      }, 2000);

    } catch (err) {
      console.error("Job creation failed:", err);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.3 }}
      className="space-y-4"
    >
      <div className="flex gap-3">
        <button
          onClick={() => createJob("merge")}
          className="flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground hover:scale-[1.02]"
        >
          <Merge className="h-4 w-4" />
          Merge Videos
        </button>

        <button
          onClick={() => createJob("sync")}
          className="flex items-center gap-2 rounded-lg border border-primary/40 bg-primary/10 px-6 py-3 text-sm font-semibold text-primary hover:scale-[1.02]"
        >
          <Zap className="h-4 w-4" />
          Synchronize
        </button>
      </div>

      {jobStatus && (
        <div className="text-sm text-muted-foreground">
          Status: {jobStatus}
        </div>
      )}
    </motion.div>
  );
};

export default MergeControls;