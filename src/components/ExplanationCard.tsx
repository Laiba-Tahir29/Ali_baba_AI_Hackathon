import React, { useState } from "react";
import { Stethoscope, CheckCircle2, ShieldAlert, Sparkles, ClipboardEdit, Check, PenTool } from "lucide-react";
import { CLINICAL_DISCLAIMER } from "../config/constants";

interface ExplanationCardProps {
  explanation: string;
  riskLevel?: "low" | "medium" | "high";
}

export const ExplanationCard: React.FC<ExplanationCardProps> = ({ explanation, riskLevel = "high" }) => {
  const [isAcknowledged, setIsAcknowledged] = useState(false);
  const [acknowledgedTimestamp, setAcknowledgedTimestamp] = useState<string | null>(null);
  const [physicianNotes, setPhysicianNotes] = useState("");

  const handleAcknowledge = () => {
    const nextState = !isAcknowledged;
    setIsAcknowledged(nextState);
    if (nextState) {
      setAcknowledgedTimestamp(new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    } else {
      setAcknowledgedTimestamp(null);
    }
  };

  return (
    <div className="bg-white rounded-2xl border border-[#00685f]/30 p-5 sm:p-6 shadow-[0_4px_20px_rgba(0,0,0,0.04)] relative overflow-hidden">
      {/* Top Accent Strip */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-[#00685f]"></div>

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

        <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#00685f] bg-[#00685f]/10 px-2.5 py-1 rounded-full border border-[#00685f]/20">
          <Sparkles className="w-3.5 h-3.5" />
          Clinical Synthesis Engine
        </span>
      </div>

      {/* Main Synthesized Narrative Text */}
      <div className="p-4 sm:p-5 rounded-xl bg-[#00685f]/5 border border-[#00685f]/15 mb-5">
        <p className="text-sm text-slate-800 leading-relaxed font-normal">
          {explanation}
        </p>
      </div>

      {/* Doctor Action & Scratchpad */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 pt-2 border-t border-[#e1e3e4]">
        {/* Left: Physician Scratchpad / Care Plan Notes */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5 flex items-center gap-1.5">
            <PenTool className="w-3.5 h-3.5 text-[#00685f]" />
            Attending Physician Clinical Notes (Optional):
          </label>
          <textarea
            value={physicianNotes}
            onChange={(e) => setPhysicianNotes(e.target.value)}
            placeholder="Add specific clinical actions, medication adjustments, or next follow-up dates..."
            rows={2}
            className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:border-[#00685f] focus:ring-1 focus:ring-[#00685f] bg-slate-50/50 outline-none resize-none placeholder:text-slate-400"
          />
        </div>

        {/* Right: Triage Review Sign-off */}
        <div className="flex flex-col justify-end">
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between h-full">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="acknowledge-triage-checkbox"
                  checked={isAcknowledged}
                  onChange={handleAcknowledge}
                  className="w-4 h-4 text-[#00685f] rounded border-slate-300 focus:ring-[#00685f] cursor-pointer"
                />
                <label
                  htmlFor="acknowledge-triage-checkbox"
                  className="text-xs font-bold text-[#191c1d] cursor-pointer"
                >
                  Mark as Reviewed by Attending Physician
                </label>
              </div>

              {isAcknowledged && (
                <span className="text-[11px] font-semibold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded flex items-center gap-1">
                  <Check className="w-3 h-3" />
                  Reviewed
                </span>
              )}
            </div>

            <p className="text-[11px] text-slate-500 mt-2">
              {isAcknowledged ? (
                <span className="text-emerald-700 font-medium">
                  Signed by Dr. S. Jenkins at {acknowledgedTimestamp} • Ready for patient encounter
                </span>
              ) : (
                "Review the above factors and historical document snippets before confirming triage recommendations."
              )}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};
