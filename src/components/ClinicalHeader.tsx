
import React from "react";
import { Activity, RefreshCw, User } from "lucide-react";
import { CLINICAL_HEADER_SUBTITLE, USE_MOCK } from "../config/constants";

interface ClinicalHeaderProps {
  onReset?: () => void;
  showReset?: boolean;
}

export const ClinicalHeader: React.FC<ClinicalHeaderProps> = ({
  onReset,
  showReset = false,
}) => {
  return (
    <header className="bg-white border-b border-[#e1e3e4] sticky top-0 z-30 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">

          {/* Brand & Triage Label */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-[#00685f] flex items-center justify-center text-white shadow-xs">
              <Activity className="w-6 h-6 text-white" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span className="font-bold text-lg text-[#191c1d] tracking-tight">
                  Cardiovascular Risk Summarizer
                </span>

                <span className="hidden sm:inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-[#00685f]/10 text-[#00685f] border border-[#00685f]/20">
                  Clinical Triage Tool
                </span>
              </div>

              <p className="text-xs text-[#585e6c]">
                {CLINICAL_HEADER_SUBTITLE}
              </p>
            </div>
          </div>

          {/* Right Actions & Clinical Review Profile */}
          <div className="flex items-center gap-3 sm:gap-4">

            {/* Demo Mode Indicator */}
            {USE_MOCK && (
              <span className="hidden md:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                Demo Simulation Mode
              </span>
            )}

            {/* New Analysis Button */}
            {showReset && onReset && (
              <button
                onClick={onReset}
                id="header-new-upload-btn"
                className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-[#00685f]/10 text-[#00685f] hover:bg-[#00685f]/20 transition-colors cursor-pointer"
                title="Start a new patient analysis"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">New Analysis</span>
              </button>
            )}

            <div className="h-6 w-px bg-slate-200 hidden sm:block"></div>

            {/* Clinical Review Profile */}
            <div className="flex items-center gap-2.5 pl-1">
              <div className="w-8 h-8 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-700 font-medium text-xs">
                <User className="w-4 h-4 text-[#00685f]" />
              </div>

              <div className="hidden lg:block text-right">
                <p className="text-xs font-semibold text-[#191c1d]">
                  Cardiology Triage
                </p>
                <p className="text-[11px] text-[#585e6c]">
                  Clinical Review
                </p>
              </div>
            </div>

          </div>
        </div>
      </div>
    </header>
  );
};

