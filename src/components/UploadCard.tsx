
import React, { useState, useRef, DragEvent, ChangeEvent } from "react";
import {
  UploadCloud,
  FileText,
  AlertCircle,
  ArrowRight,
  ShieldCheck,
  FileCheck,
} from "lucide-react";

interface UploadCardProps {
  onAnalyze: (file: File) => void;
  isLoading: boolean;
}

export const UploadCard: React.FC<UploadCardProps> = ({
  onAnalyze,
  isLoading,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setErrorMsg(null);

    if (
      !file.name.toLowerCase().endsWith(".pdf") &&
      file.type !== "application/pdf"
    ) {
      setErrorMsg(
        "Please upload a valid PDF document containing clinical notes."
      );
      return;
    }

    if (file.size > 25 * 1024 * 1024) {
      setErrorMsg(
        "File size exceeds 25MB limit. Please provide a smaller document."
      );
      return;
    }

    setSelectedFile(file);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0]);
    }
  };

  const handleTriggerAnalysis = () => {
    if (!selectedFile || isLoading) return;

    onAnalyze(selectedFile);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;

    if (bytes < 1024 * 1024) {
      return `${(bytes / 1024).toFixed(1)} KB`;
    }

    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="bg-white rounded-2xl border border-[#e1e3e4] shadow-[0_4px_20px_rgba(0,0,0,0.04)] overflow-hidden">

        {/* Header */}
        <div className="px-6 py-5 border-b border-[#e1e3e4] bg-slate-50/50 flex items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-[#191c1d] flex items-center gap-2">
              <FileText className="w-5 h-5 text-[#00685f]" />
              Historical Cardiology Reports Ingestion
            </h2>

            <p className="text-xs text-[#585e6c] mt-0.5">
              Upload a multi-encounter PDF containing clinical notes, lab
              panels, and recorded vitals.
            </p>
          </div>

          <span className="hidden sm:inline-flex items-center gap-1 text-[11px] font-semibold text-[#00685f] bg-[#00685f]/10 px-2.5 py-1 rounded-full whitespace-nowrap">
            <ShieldCheck className="w-3.5 h-3.5" />
            Secure Clinical Ingestion
          </span>
        </div>

        <div className="p-6 sm:p-8 space-y-6">

          {/* Upload Area */}
          <div
            id="pdf-upload-dropzone"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => {
              if (!isLoading) {
                fileInputRef.current?.click();
              }
            }}
            className={`relative rounded-2xl border-2 border-dashed transition-all duration-200 p-8 sm:p-10 text-center flex flex-col items-center justify-center min-h-[230px] ${
              isLoading
                ? "cursor-not-allowed border-slate-200 bg-slate-50"
                : isDragging
                ? "cursor-pointer border-[#00685f] bg-[#00685f]/5 ring-4 ring-[#00685f]/10"
                : selectedFile
                ? "cursor-pointer border-emerald-300 bg-emerald-50/30"
                : "cursor-pointer border-slate-300 hover:border-[#00685f] hover:bg-slate-50/80 bg-[#f8f9fa]"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={handleFileInputChange}
              id="pdf-file-input"
              disabled={isLoading}
            />

            {selectedFile ? (
              <div className="flex flex-col items-center space-y-3">
                <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shadow-sm">
                  <FileCheck className="w-7 h-7" />
                </div>

                <div>
                  <p className="text-sm font-bold text-[#191c1d] max-w-md truncate">
                    {selectedFile.name}
                  </p>

                  <p className="text-xs text-slate-500 mt-1">
                    {formatFileSize(selectedFile.size)} • PDF ready for
                    clinical extraction
                  </p>
                </div>

                {!isLoading && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();

                      setSelectedFile(null);
                      setErrorMsg(null);

                      if (fileInputRef.current) {
                        fileInputRef.current.value = "";
                      }
                    }}
                    className="text-xs text-rose-600 hover:text-rose-700 underline font-medium cursor-pointer"
                  >
                    Change or remove document
                  </button>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-[#00685f]/10 text-[#00685f] flex items-center justify-center">
                  <UploadCloud className="w-8 h-8" />
                </div>

                <div>
                  <p className="text-sm sm:text-base font-semibold text-[#191c1d]">
                    Drag and drop your patient PDF here
                  </p>

                  <p className="text-sm text-[#585e6c] mt-1">
                    or{" "}
                    <span className="text-[#00685f] underline font-medium">
                      browse files
                    </span>
                  </p>

                  <p className="text-xs text-slate-400 mt-3">
                    Multi-page clinical notes, lab reports, discharge
                    summaries • PDF up to 25MB
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Security / Pipeline Hint */}
          <div className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-[11px] text-slate-500">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Secure document ingestion
            </span>

            <span className="hidden sm:inline text-slate-300">•</span>

            <span>
              PDF → Clinical extraction → Risk synthesis
            </span>
          </div>

          {/* Validation Error */}
          {errorMsg && (
            <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Analyze Button */}
          <div className="pt-1">
            <button
              id="analyze-reports-submit-btn"
              type="button"
              disabled={!selectedFile || isLoading}
              onClick={handleTriggerAnalysis}
              className={`w-full py-3.5 px-6 rounded-xl font-semibold text-sm flex items-center justify-center gap-2 transition-all shadow-sm ${
                !selectedFile || isLoading
                  ? "bg-slate-200 text-slate-400 cursor-not-allowed border border-slate-200"
                  : "bg-[#00685f] text-white hover:bg-[#005049] active:scale-[0.99] cursor-pointer shadow-[#00685f]/20"
              }`}
            >
              {isLoading ? (
                <>
                  <span className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
                  <span>Analyzing Clinical Reports...</span>
                </>
              ) : (
                <>
                  <span>Analyze Reports & Consolidate Risk</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-slate-50 border-t border-[#e1e3e4] text-[11px] text-[#585e6c] flex flex-col sm:flex-row items-center justify-between gap-2">
          <span>
            Supported schemas: HL7 CCD, Clinical summaries, PDF scans
          </span>

          <span className="text-slate-400">
            Strictly for physician review
          </span>
        </div>
      </div>
    </div>
  );
};

