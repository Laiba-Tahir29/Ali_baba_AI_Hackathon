import React, { useState } from "react";
import { AlertTriangle, CheckCircle, Info, ShieldAlert, FileText, Printer, ArrowLeft } from "lucide-react";
import { RISK_CONFIG, RiskLevel } from "../config/constants";
import { RiskAnalysis } from "../types/clinical";

interface RiskBadgeProps {
  risk: RiskAnalysis;
  patientMeta?: {
    id: string;
    name: string;
    mrn: string;
    analyzedAt?: string;
  };
  onNewAnalysis?: () => void;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({ risk, patientMeta, onNewAnalysis }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const riskLevelKey = (risk.risk_level || "high").toLowerCase() as RiskLevel;

  const config = RISK_CONFIG[riskLevelKey] || RISK_CONFIG.high;



  

  const handlePrint = () => {
    window.print();
  };

  // FIX 1: Format risk_score percentage correctly
  const riskScoreValue = Number(risk.risk_score ?? 0);
  const formattedRiskScore =
    Number.isFinite(riskScoreValue)
      ? `${(riskScoreValue > 1 ? riskScoreValue : riskScoreValue * 100).toFixed(1).replace(/\.0$/, "")}%`
      : "0%";
  
  // FIX 2: Show "None" when no primary factor exists
  const primaryFactor =
    risk.top_3_factors?.[0] || risk.top_factors?.[0] || "None — no elevated factors";

  return (
    <div className="w-full bg-white rounded-2xl border border-[#e1e3e4] p-5 sm:p-6 shadow-[0_4px_20px_rgba(0,0,0,0.04)] mb-6">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-5">
        
        {/* Left: Prominent Risk Flag Pill */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4">
          <div
            className={`inline-flex items-center gap-2.5 px-4 py-2.5 rounded-xl border text-sm font-bold shadow-xs ${config.badgeBg}`}
          >
            <span className={`w-3 h-3 rounded-full ${config.dotColor} animate-pulse shrink-0`} />
            <span className="tracking-tight text-base sm:text-lg">
              {config.label}
            </span>

            {/* Info tooltip button */}
            <div className="relative inline-block ml-1">
              <button
                type="button"
                onMouseEnter={() => setShowTooltip(true)}
                onMouseLeave={() => setShowTooltip(false)}
                onClick={() => setShowTooltip(!showTooltip)}
                className="text-slate-500 hover:text-slate-800 p-0.5 rounded-full hover:bg-black/5 transition-colors cursor-pointer"
                aria-label="Clinical Disclaimer Info"
              >
                <Info className="w-4 h-4" />
              </button>

              {showTooltip && (
                <div className="absolute left-1/2 -translate-x-1/2 bottom-full mb-2 w-64 p-3 bg-slate-900 text-white text-xs rounded-xl shadow-xl z-50 pointer-events-none leading-relaxed">
                  <div className="font-semibold text-slate-200 mb-1 flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                    Clinical Safety Notice
                  </div>
                  Indicative only, not a diagnosis. Risk flag is computed from historical report consolidation for doctor review.
                  <div className="w-2 h-2 bg-slate-900 rotate-45 absolute -bottom-1 left-1/2 -translate-x-1/2"></div>
                </div>
              )}
            </div>
          </div>

          {/* Numeric Score Pill & Risk Factor Pill */}
          <div className="flex items-center gap-2 flex-wrap">
            <div className="px-3 py-1.5 rounded-lg bg-slate-100 border border-slate-200 text-xs text-slate-700">
              <span className="text-slate-500">Calculated Score:</span>{" "}
              <span className="font-bold text-[#191c1d]">{formattedRiskScore}</span>
            </div>
            <div className="px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-600">
              <span className="text-slate-500">Primary driver:</span>{" "}
              <span className="font-semibold text-[#191c1d]">{primaryFactor}</span>
            </div>
          </div>
        </div>

        {/* Right: Patient Metadata Bar & Export Action */}
        <div className="flex items-center gap-3 self-end lg:self-center">
          {patientMeta && (
            <div className="hidden md:flex flex-col text-right pr-3 border-r border-slate-200">
              <span className="text-xs font-bold text-[#191c1d]">{patientMeta.name}</span>
              <span className="text-[11px] text-slate-500">
                {patientMeta.id} • {patientMeta.mrn}
              </span>
            </div>
          )}

          <button
            onClick={handlePrint}
            id="print-summary-btn"
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors border border-slate-200 cursor-pointer"
            title="Print Clinical Summary"
          >
            <Printer className="w-3.5 h-3.5 text-slate-600" />
            <span className="hidden sm:inline">Print Report</span>
          </button>

          {onNewAnalysis && (
            <button
              onClick={onNewAnalysis}
              id="new-analysis-btn"
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold bg-[#00685f] hover:bg-[#005049] text-white transition-colors cursor-pointer shadow-xs"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>New Patient</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};