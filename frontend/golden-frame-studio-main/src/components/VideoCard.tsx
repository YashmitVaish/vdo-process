import { useState } from "react";
import { motion } from "framer-motion";
import { Film, Monitor, Clock, Link2, X } from "lucide-react";

export interface VideoFile {
  id: string;
  name: string;
  size: number;
  file: File;
  url: string;
  // Mock metadata
  resolution: string;
  frameRate: string;
  duration: string;
  aspectRatio: string;
}

interface VideoCardProps {
  video: VideoFile;
  onRemove: (id: string) => void;
  index: number;
}

const VideoCard = ({ video, onRemove, index }: VideoCardProps) => {
  const [isHovered, setIsHovered] = useState(false);

  const formatSize = (bytes: number) => {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.3, delay: index * 0.05 }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className="group relative overflow-hidden rounded-lg border border-border bg-card transition-all duration-300 hover:border-primary/40 hover:gold-border-glow"
    >
      {/* Thumbnail / Preview */}
      <div className="relative aspect-video bg-muted overflow-hidden">
        <video
          src={video.url}
          className="h-full w-full object-cover"
          muted
          onMouseEnter={(e) => (e.target as HTMLVideoElement).play()}
          onMouseLeave={(e) => {
            const v = e.target as HTMLVideoElement;
            v.pause();
            v.currentTime = 0;
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background/90 via-transparent to-transparent" />

        {/* Remove button */}
        <button
          onClick={() => onRemove(video.id)}
          className="absolute right-2 top-2 rounded-full bg-background/80 p-1.5 opacity-0 transition-opacity group-hover:opacity-100 hover:bg-destructive/80"
        >
          <X className="h-3 w-3 text-foreground" />
        </button>

        {/* Duration badge */}
        <span className="absolute bottom-2 right-2 rounded bg-background/80 px-2 py-0.5 font-mono text-xs text-foreground">
          {video.duration}
        </span>
      </div>

      {/* Info */}
      <div className="p-3 space-y-2">
        <p className="truncate text-sm font-medium text-foreground">{video.name}</p>
        <div className="flex flex-wrap gap-2 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <Monitor className="h-3 w-3 text-primary" />
            {video.resolution}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3 text-primary" />
            {video.frameRate}
          </span>
          <span className="flex items-center gap-1">
            <Film className="h-3 w-3 text-primary" />
            {video.aspectRatio}
          </span>
        </div>
        <p className="text-xs text-muted-foreground">{formatSize(video.size)}</p>
      </div>

      {/* Hover overlay with link */}
      {isHovered && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="absolute bottom-0 left-0 right-0 bg-card/95 border-t border-border p-3"
        >
          <div className="flex items-center gap-2 text-xs text-primary font-mono">
            <Link2 className="h-3 w-3" />
            <span className="truncate">/api/videos/{video.id}</span>
          </div>
        </motion.div>
      )}
    </motion.div>
  );
};

export default VideoCard;
