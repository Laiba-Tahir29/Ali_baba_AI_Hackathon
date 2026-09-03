import React from "react";
import { Stethoscope, Sparkles } from "lucide-react";

interface ExplanationCardProps {
  explanation: string;
  riskLevel?: "low" | "medium" | "high";
}

export const ExplanationCard: React.FC<ExplanationCardProps> = ({
  explanation,
  riskLevel = "high",
}) => {
  return (
    <div className="bg-white rounded-2xl border border-[#00685f]/30 p-5 sm:p-6 shadow-[0_4px_20px_rgba(0,0,0,0.04)] relative overflow-hidden">

      {/* Top Accent Strip */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-[#00685f]"></div>

      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-[#e1e3e4]">
        <div>
          <h3 className="text-base font-bold text-[#191c1d] flex items-center gap-2">
            <Stethoscope className="w-4 h-4 text-[#00685f]" />
            Summary for Doctor Review
          </h3>

          <p className="text-xs text-[#585e6c]">
            Multi-encounter synthesized clinical narrative and trajectory evaluation
          </p>
        </div>

        {/* Clinical Synthesis Badge */}
        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#00685f] bg-[#00685f]/10 px-2.5 py-1 rounded-full border border-[#00685f]/20">
          <Sparkles className="w-3.5 h-3.5" />
          Clinical Synthesis Engine
        </span>
      </div>

      {/* Main Synthesized Narrative */}
      <div className="p-4 sm:p-5 rounded-xl bg-[#00685f]/5 border border-[#00685f]/15">
        <p className="text-sm text-slate-800 leading-relaxed font-normal">
          {explanation}
        </p>
      </div>

    </div>
  );
};