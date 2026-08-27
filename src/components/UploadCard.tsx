import React, { useState, useRef, DragEvent, ChangeEvent } from "react";
import { UploadCloud, FileText, CheckCircle2, AlertCircle, ArrowRight, ShieldCheck, FileCheck, Sparkles } from "lucide-react";
import { SAMPLE_PATIENT_PRESETS } from "../config/constants";

interface UploadCardProps {
  onAnalyze: (file: File) => void;
  onSelectPreset?: (preset: typeof SAMPLE_PATIENT_PRESETS[0]) => void;
  isLoading: boolean;
}

export const UploadCard: React.FC<UploadCardProps> = ({ onAnalyze, onSelectPreset, isLoading }) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (file: File) => {
    setErrorMsg(null);
    if (!file.name.toLowerCase().endsWith(".pdf") && file.type !== "application/pdf") {
      setErrorMsg("Please upload a valid PDF document containing clinical notes.");
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setErrorMsg("File size exceeds 25MB limit. Please provide a smaller document.");
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
    if (!selectedFile) return;
    onAnalyze(selectedFile);
  };

  const handlePresetClick = (preset: typeof SAMPLE_PATIENT_PRESETS[0]) => {
    setErrorMsg(null);
    // Create a virtual File object for the preset
    const fakeBlob = new Blob(["Clinical Encounters Mock PDF Content"], { type: "application/pdf" });
    const virtualFile = new File([fakeBlob], preset.filename, { type: "application/pdf" });
    setSelectedFile(virtualFile);
    if (onSelectPreset) {
      onSelectPreset(preset);
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div className="w-full max-w-3xl mx-auto">
      {/* Card Header & Title */}
      <div className="bg-white rounded-2xl border border-[#e1e3e4] shadow-[0_4px_20px_rgba(0,0,0,0.04)] overflow-hidden">
        <div className="px-6 py-5 border-b border-[#e1e3e4] bg-slate-50/50 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-[#191c1d] flex items-center gap-2">
              <FileText className="w-5 h-5 text-[#00685f]" />
              Historical Cardiology Reports Ingestion
            </h2>
            <p className="text-xs text-[#585e6c] mt-0.5">
              Upload multi-encounter PDF containing clinic notes, lab panels, and recorded vitals.
            </p>
          </div>
          <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-[#00685f] bg-[#00685f]/10 px-2.5 py-1 rounded-full">
            <ShieldCheck className="w-3.5 h-3.5" />
            HIPAA Compliant Ingestion
          </span>
        </div>

        <div className="p-6 sm:p-8 space-y-6">
          {/* Dropzone */}
          <div
            id="pdf-upload-dropzone"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`relative rounded-xl border-2 border-dashed transition-all duration-200 cursor-pointer p-8 sm:p-10 text-center flex flex-col items-center justify-center ${
              isDragging
                ? "border-[#00685f] bg-[#00685f]/5 ring-4 ring-[#00685f]/10"
                : selectedFile
                ? "border-emerald-300 bg-emerald-50/30"
                : "border-slate-300 hover:border-[#00685f] hover:bg-slate-50/80 bg-[#f8f9fa]"
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,application/pdf"
              className="hidden"
              onChange={handleFileInputChange}
              id="pdf-file-input"
            />

            {selectedFile ? (
              <div className="flex flex-col items-center space-y-3">
                <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center shadow-xs">
                  <FileCheck className="w-7 h-7" />
                </div>
                <div>
                  <p className="text-sm font-bold text-[#191c1d] max-w-md truncate">
                    {selectedFile.name}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {formatFileSize(selectedFile.size)} • PDF Ready for Clinical Extraction
                  </p>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    setSelectedFile(null);
                    if (fileInputRef.current) fileInputRef.current.value = "";
                  }}
                  className="text-xs text-rose-600 hover:text-rose-700 underline font-medium cursor-pointer"
                >
                  Change or remove document
                </button>
              </div>
            ) : (
              <div className="flex flex-col items-center space-y-3">
                <div className="w-14 h-14 rounded-full bg-[#00685f]/10 text-[#00685f] flex items-center justify-center">
                  <UploadCloud className="w-7 h-7" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-[#191c1d]">
                    Drag and drop patient PDF here, or <span className="text-[#00685f] underline">browse files</span>
                  </p>
                  <p className="text-xs text-[#585e6c] mt-1">
                    Accepts multi-page clinical notes, hospital discharge summaries, or lab records (.pdf up to 25MB)
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Validation Error */}
          {errorMsg && (
            <div className="p-3.5 rounded-lg bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Preset Quick Select for Physicians */}
          <div className="border-t border-[#e1e3e4] pt-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#585e6c] flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-[#00685f]" />
                Or ingest verified sample patient records:
              </span>
              <span className="text-[11px] text-slate-400">Click to load</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
              {SAMPLE_PATIENT_PRESETS.map((preset) => {
                const isCurrent = selectedFile?.name === preset.filename;
                const badgeColor =
                  preset.expectedRisk === "high"
                    ? "bg-rose-50 text-rose-700 border-rose-200"
                    : preset.expectedRisk === "medium"
                    ? "bg-amber-50 text-amber-700 border-amber-200"
                    : "bg-emerald-50 text-emerald-700 border-emerald-200";

                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => handlePresetClick(preset)}
                    className={`text-left p-3 rounded-xl border transition-all cursor-pointer ${
                      isCurrent
                        ? "border-[#00685f] bg-[#00685f]/5 ring-2 ring-[#00685f]/20 shadow-xs"
                        : "border-[#e1e3e4] hover:border-slate-300 bg-white hover:bg-slate-50/80"
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-bold text-[#191c1d]">{preset.id}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded font-semibold border ${badgeColor}`}>
                        {preset.expectedRisk.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-xs font-medium text-slate-700 truncate">{preset.name}</p>
                    <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                      {preset.description}
                    </p>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Action Button */}
          <div className="pt-2">
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
              <span>Analyze Reports & Consolidate Risk</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Footer info within card */}
        <div className="px-6 py-3 bg-slate-50 border-t border-[#e1e3e4] text-[11px] text-[#585e6c] flex items-center justify-between">
          <span>Supported schemas: HL7 CCD, Clinical summaries, PDF scans</span>
          <span className="text-slate-400">Strictly for physician review</span>
        </div>
      </div>
    </div>
  );
};
