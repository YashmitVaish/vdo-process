import { useState, useCallback } from "react";
import { Upload, Film } from "lucide-react";
import { motion } from "framer-motion";

interface VideoUploaderProps {
  onUpload: (files: File[]) => void;
}

const VideoUploader = ({ onUpload }: VideoUploaderProps) => {
  const [isDragging, setIsDragging] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files).filter((f) =>
        f.type.startsWith("video/")
      );
      if (files.length) onUpload(files);
    },
    [onUpload]
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      if (files.length) onUpload(files);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="relative rounded-2xl border border-yellow-500/20 
      bg-gradient-to-br from-black via-zinc-900 to-black
      shadow-[0_0_40px_rgba(255,200,0,0.05)]
      backdrop-blur-md p-16 overflow-hidden"
    >
      {/* Soft radial gold glow */}
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,200,0,0.08),transparent_60%)] pointer-events-none" />

      <label
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center gap-6 cursor-pointer transition-all duration-300 ${
          isDragging
            ? "scale-105"
            : "hover:scale-[1.02]"
        }`}
      >
        <input
          type="file"
          accept="video/*"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />

        {/* Animated Icon */}
        <motion.div
          animate={
            isDragging
              ? { scale: 1.15, rotate: 6 }
              : { scale: 1, rotate: 0 }
          }
          transition={{ duration: 0.3 }}
          className="rounded-2xl bg-gradient-to-br from-yellow-500/20 to-amber-400/10 p-6 shadow-[0_0_25px_rgba(255,200,0,0.15)]"
        >
          {isDragging ? (
            <Film className="h-10 w-10 text-yellow-400" />
          ) : (
            <Upload className="h-10 w-10 text-yellow-400" />
          )}
        </motion.div>

        {/* Text */}
        <div className="text-center space-y-2">
          <p className="text-xl font-semibold text-zinc-200 tracking-wide">
            {isDragging ? "Release to Upload" : "Drag & Drop Your Videos"}
          </p>

          <p className="text-sm text-zinc-500 tracking-wide">
            or click to browse • MP4, MOV, AVI, MKV
          </p>
        </div>
      </label>
    </motion.div>
  );
};

export default VideoUploader;