import { useState, useCallback } from "react";
import { Upload, Film } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

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
    >
      <label
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`relative flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-12 cursor-pointer transition-all duration-300 ${
          isDragging
            ? "upload-zone-active border-primary"
            : "border-border hover:border-primary/50 hover:bg-muted/30"
        }`}
      >
        <input
          type="file"
          accept="video/*"
          multiple
          onChange={handleFileSelect}
          className="hidden"
        />
        <motion.div
          animate={isDragging ? { scale: 1.1, rotate: 5 } : { scale: 1, rotate: 0 }}
          className="rounded-full bg-primary/10 p-4"
        >
          {isDragging ? (
            <Film className="h-8 w-8 text-primary" />
          ) : (
            <Upload className="h-8 w-8 text-primary" />
          )}
        </motion.div>
        <div className="text-center">
          <p className="text-lg font-medium text-foreground">
            {isDragging ? "Drop your videos here" : "Drag & drop videos"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            or click to browse • MP4, MOV, AVI, MKV
          </p>
        </div>
      </label>
    </motion.div>
  );
};

export default VideoUploader;
