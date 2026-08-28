import React from "react";
import { AlertOctagon, RefreshCw, UploadCloud, FileWarning } from "lucide-react";
import { ErrorDetails } from "../types/clinical";

interface ErrorStateProps {
  error: ErrorDetails | null;
  onRetry: () => void;
  onNewUpload: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({ error, onRetry, onNewUpload }) => {
  return (
    <div className="w-full max-w-xl mx-auto py-12 px-4">
      <div className="bg-white rounded-2xl border border-rose-200 p-8 sm:p-10 shadow-[0_4px_20px_rgba(0,0,0,0.04)] text-center space-y-6">
        
        {/* Error Graphic */}
        <div className="w-16 h-16 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center mx-auto shadow-xs">
          <AlertOctagon className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <span className="text-[11px] font-bold uppercase tracking-wider text-rose-700 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded-full">
            Analysis Ingestion Issue
          </span>
          <h3 className="text-xl font-bold text-[#191c1d]">
            {error?.title || "Unable to Complete Risk Synthesis"}
          </h3>
          <p className="text-xs text-slate-600 max-w-md mx-auto leading-relaxed">
            {error?.message || "An error occurred while parsing clinical reports or connecting to the analysis service. Please verify the document format or try again."}
          </p>
          {error?.code && (
            <p className="text-[10px] font-mono text-slate-400">
              Error Ref: {error.code}
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-3">
          <button
            type="button"
            onClick={onRetry}
            id="error-retry-btn"
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#00685f] hover:bg-[#005049] text-white transition-colors flex items-center justify-center gap-2 cursor-pointer shadow-xs"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Retry Analysis</span>
          </button>

          <button
            type="button"
            onClick={onNewUpload}
            id="error-new-upload-btn"
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition-colors border border-slate-200 flex items-center justify-center gap-2 cursor-pointer"
          >
            <UploadCloud className="w-3.5 h-3.5" />
            <span>Select Another Document</span>
          </button>
        </div>

        {/* Clinical Note */}
        <div className="pt-4 border-t border-slate-100 text-[11px] text-slate-400">
          Ensure PDF documents contain machine-readable or clean scanned text.
        </div>
      </div>
    </div>
  );
};
