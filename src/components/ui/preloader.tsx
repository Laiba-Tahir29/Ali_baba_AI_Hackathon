import React from "react";
import { motion, useReducedMotion } from "framer-motion";
import { cn } from "../../lib/utils";

export interface PreloaderProps {
  /** The current status message or stage */
  text?: string;
  /** Optional secondary subtitle or detail */
  subtext?: string;
  /** Clinical animation style: 'line' | 'dots' | 'minimal' */
  variant?: "line" | "dots" | "minimal" | "circle";
  /** Percentage completion value (0-100) */
  progress?: number;
  /** Additional container styling */
  className?: string;
  /** Primary accent color class */
  color?: string;
}

export const Preloader: React.FC<PreloaderProps> = ({
  text,
  subtext,
  variant = "line",
  progress,
  className,
  color = "#00685f",
}) => {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center p-6 text-center select-none",
        className
      )}
      role="status"
      aria-live="polite"
    >
      {/* Visual Animation Container */}
      <div className="relative flex items-center justify-center mb-6 h-16 w-full max-w-xs">
        {variant === "line" && (
          <div className="w-full flex flex-col items-center gap-2">
            <div className="relative w-48 h-1.5 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
              {shouldReduceMotion ? (
                <div
                  className="h-full bg-[#00685f] rounded-full transition-all duration-300"
                  style={{ width: `${progress ?? 60}%` }}
                />
              ) : (
                <motion.div
                  className="absolute top-0 bottom-0 bg-[#00685f] rounded-full"
                  initial={{ left: "-40%", width: "40%" }}
                  animate={{
                    left: ["-40%", "100%"],
                    width: ["40%", "60%", "40%"],
                  }}
                  transition={{
                    repeat: Infinity,
                    duration: 1.4,
                    ease: [0.4, 0, 0.2, 1],
                  }}
                />
              )}
            </div>
            {/* Subtle Clinical ECG line glow accent */}
            <div className="flex items-center gap-1.5 opacity-60">
              <span className="w-1.5 h-1.5 rounded-full bg-[#00685f]" />
              <span className="w-8 h-px bg-gradient-to-r from-[#00685f] to-transparent" />
            </div>
          </div>
        )}

        {variant === "dots" && (
          <div className="flex items-center gap-2">
            {[0, 1, 2, 3].map((i) => (
              <motion.div
                key={i}
                className="w-2.5 h-2.5 rounded-full bg-[#00685f]"
                initial={{ opacity: 0.3, scale: 0.8 }}
                animate={
                  shouldReduceMotion
                    ? { opacity: 0.8 }
                    : {
                        opacity: [0.3, 1, 0.3],
                        scale: [0.8, 1.1, 0.8],
                      }
                }
                transition={{
                  repeat: Infinity,
                  duration: 1.2,
                  delay: i * 0.15,
                  ease: "easeInOut",
                }}
              />
            ))}
          </div>
        )}

        {variant === "minimal" && (
          <div className="relative flex items-center justify-center">
            <div className="w-10 h-10 rounded-full border-2 border-slate-200 border-t-[#00685f] animate-spin" />
            {typeof progress === "number" && (
              <span className="absolute text-[10px] font-bold text-[#00685f]">
                {progress}%
              </span>
            )}
          </div>
        )}

        {variant === "circle" && (
          <div className="relative w-14 h-14 flex items-center justify-center">
            <svg className="w-full h-full -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-100 stroke-current"
                strokeWidth="3"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <motion.path
                className="text-[#00685f] stroke-current"
                strokeWidth="3"
                strokeDasharray="100, 100"
                strokeDashoffset={100 - (progress ?? 70)}
                strokeLinecap="round"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
                transition={{ duration: 0.3, ease: "easeOut" }}
              />
            </svg>
            <span className="absolute text-[11px] font-bold text-[#00685f]">
              {progress ?? 0}%
            </span>
          </div>
        )}
      </div>

      {/* Rotating Status Text */}
      {text && (
        <motion.div
          key={text}
          initial={shouldReduceMotion ? { opacity: 0 } : { opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -4 }}
          transition={{ duration: 0.22, ease: "easeOut" }}
          className="space-y-1"
        >
          <p className="text-lg font-bold text-[#191c1d] tracking-tight">
            {text}
          </p>
          {subtext && (
            <p className="text-xs text-[#585e6c] max-w-sm mx-auto">
              {subtext}
            </p>
          )}
        </motion.div>
      )}
    </div>
  );
};

export default Preloader;
