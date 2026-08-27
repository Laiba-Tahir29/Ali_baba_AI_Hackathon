import React, { useState, useEffect, Suspense, lazy } from "react";
import { ShieldCheck, Sparkles } from "lucide-react";
import { LOADING_STEPS, LOADING_STATUS_INTERVAL_MS } from "../config/constants";

// Lazy-load Preloader component per performance guardrail
const Preloader = lazy(() => import("./ui/preloader"));

interface LoadingStateProps {
  fileName?: string;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ fileName }) => {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStepIndex((prev) => (prev + 1) % LOADING_STEPS.length);
    }, LOADING_STATUS_INTERVAL_MS);

    return () => clearInterval(timer);
  }, []);

  const progressPercentage = Math.round(((currentStepIndex + 1) / LOADING_STEPS.length) * 100);

  return (
    <div className="w-full max-w-xl mx-auto py-12 px-4">
      <div className="bg-white rounded-2xl border border-[#e1e3e4] p-8 sm:p-10 shadow-[0_4px_20px_rgba(0,0,0,0.04)] text-center space-y-6">
        
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#00685f]/10 text-[#00685f]">
          <Sparkles className="w-3.5 h-3.5 animate-pulse" />
          <span>Multi-Encounter Synthesis Pipeline</span>
        </div>

        {/* Calm minimal React Bits Preloader replacing old spinner */}
        <Suspense
          fallback={
            <div className="h-28 flex flex-col items-center justify-center space-y-3">
              <div className="w-48 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                <div className="w-1/2 h-full bg-[#00685f] rounded-full animate-pulse" />
              </div>
              <p className="text-lg font-bold text-[#191c1d]">
                {LOADING_STEPS[currentStepIndex]}
              </p>
            </div>
          }
        >
          <Preloader
            variant="line"
            text={LOADING_STEPS[currentStepIndex]}
            subtext={
              fileName
                ? `Analyzing document: ${fileName}`
                : "Parsing structured vitals & unstructured notes"
            }
            progress={progressPercentage}
            className="py-1"
          />
        </Suspense>

        {/* Progress Bar & Steps Check */}
        <div className="space-y-4 pt-2">
          <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden border border-slate-200">
            <div
              className="bg-[#00685f] h-2 rounded-full transition-all duration-500 ease-out"
              style={{ width: `${progressPercentage}%` }}
            />
          </div>

          <div className="grid grid-cols-4 gap-1 text-[11px] text-slate-500 font-medium">
            {LOADING_STEPS.map((step, idx) => {
              const isDone = idx < currentStepIndex;
              const isCurrent = idx === currentStepIndex;
              return (
                <div
                  key={step}
                  className={`flex flex-col items-center gap-1 transition-colors ${
                    isCurrent
                      ? "text-[#00685f] font-semibold"
                      : isDone
                      ? "text-emerald-700"
                      : "text-slate-400"
                  }`}
                >
                  <div
                    className={`w-2 h-2 rounded-full ${
                      isCurrent
                        ? "bg-[#00685f] ring-2 ring-[#00685f]/30"
                        : isDone
                        ? "bg-emerald-500"
                        : "bg-slate-300"
                    }`}
                  />
                  <span className="truncate w-full text-center text-[10px]">
                    {step.replace("…", "")}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* HIPAA & Privacy Guarantee */}
        <div className="pt-4 border-t border-[#e1e3e4] flex items-center justify-center gap-2 text-xs text-slate-500">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Local memory parsing • Zero patient data retained in storage</span>
        </div>
      </div>
    </div>
  );
};
