import { useState } from "react";
import { motion } from "framer-motion";
import { Monitor, Clock, Maximize, Check } from "lucide-react";

interface ProcessingOptionsProps {
  videosCount: number;
}

const resolutions = [
  { label: "720p", desc: "HD • 1280×720" },
  { label: "1080p", desc: "Full HD • 1920×1080" },
  { label: "4K", desc: "Ultra HD • 3840×2160" },
];

const frameRates = [
  { label: "24 fps", desc: "Cinematic" },
  { label: "30 fps", desc: "Standard" },
  { label: "60 fps", desc: "Smooth" },
];

interface OptionGroupProps {
  title: string;
  icon: React.ReactNode;
  options: { label: string; desc: string }[];
  selected: number;
  onSelect: (i: number) => void;
}

const OptionGroup = ({ title, icon, options, selected, onSelect }: OptionGroupProps) => (
  <div className="rounded-xl border border-border bg-card p-5 space-y-4">
    <div className="flex items-center gap-2">
      {icon}
      <h3 className="text-sm font-semibold text-foreground">{title}</h3>
    </div>
    <div className="space-y-2">
      {options.map((opt, i) => (
        <button
          key={opt.label}
          onClick={() => onSelect(i)}
          className={`w-full flex items-center justify-between rounded-lg px-4 py-3 text-left transition-all duration-200 ${
            selected === i
              ? "bg-primary/10 border border-primary/40 gold-border-glow"
              : "bg-muted/30 border border-transparent hover:bg-muted/60 hover:border-border"
          }`}
        >
          <div>
            <p className={`text-sm font-medium ${selected === i ? "text-primary" : "text-foreground"}`}>
              {opt.label}
            </p>
            <p className="text-xs text-muted-foreground">{opt.desc}</p>
          </div>
          {selected === i && (
            <motion.div initial={{ scale: 0 }} animate={{ scale: 1 }}>
              <Check className="h-4 w-4 text-primary" />
            </motion.div>
          )}
        </button>
      ))}
    </div>
  </div>
);

const ProcessingOptions = ({ videosCount }: ProcessingOptionsProps) => {
  const [selRes, setSelRes] = useState(1);
  const [selFps, setSelFps] = useState(1);
  const [selAr, setSelAr] = useState(0);

  if (videosCount === 0) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.2 }}
      className="space-y-4"
    >
      <h2 className="text-lg font-semibold text-foreground">
        Processing Options
      </h2>
      <div className="grid gap-4 md:grid-cols-2">
        <OptionGroup
          title="Resolution"
          icon={<Monitor className="h-4 w-4 text-primary" />}
          options={resolutions}
          selected={selRes}
          onSelect={setSelRes}
        />
        <OptionGroup
          title="Frame Rate"
          icon={<Clock className="h-4 w-4 text-primary" />}
          options={frameRates}
          selected={selFps}
          onSelect={setSelFps}
        />
      </div>
    </motion.div>
  );
};

export default ProcessingOptions;
