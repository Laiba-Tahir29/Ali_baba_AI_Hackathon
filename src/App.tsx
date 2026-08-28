import React, { useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { ClinicalHeader } from "./components/ClinicalHeader";
import { UploadCard } from "./components/UploadCard";
import { LoadingState } from "./components/LoadingState";
import { RiskBadge } from "./components/RiskBadge";
import { FactorsGrid } from "./components/FactorsGrid";
import { FactorsChart } from "./components/FactorsChart";
import { EvidenceAccordion } from "./components/EvidenceAccordion";
import { ExplanationCard } from "./components/ExplanationCard";
import { ErrorState } from "./components/ErrorState";
import { uploadPdf, analyzePatient } from "./api/client";
import { CLINICAL_DISCLAIMER } from "./config/constants";
import { AnalysisResponse, ViewState, ErrorDetails } from "./types/clinical";
import { ShieldCheck, Info, HeartPulse } from "lucide-react";

export default function App() {
  const [viewState, setViewState] = useState<ViewState>("upload");
  const [currentFile, setCurrentFile] = useState<File | null>(null);
  const [analysisData, setAnalysisData] = useState<AnalysisResponse | null>(null);
  const [errorDetails, setErrorDetails] = useState<ErrorDetails | null>(null);

  const shouldReduceMotion = useReducedMotion();

  // Page view transition variants: short fade + 8-12px vertical slide (~220ms, easeOut)
  // Crossfade only when prefers-reduced-motion is active
  const pageVariants = {
    initial: {
      opacity: 0,
      y: shouldReduceMotion ? 0 : 10,
    },
    animate: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.22,
        ease: "easeOut",
      },
    },
    exit: {
      opacity: 0,
      y: shouldReduceMotion ? 0 : -8,
      transition: {
        duration: 0.18,
        ease: "easeOut",
      },
    },
  };

  const runAnalysisPipeline = async (file: File) => {
    setCurrentFile(file);
    setViewState("loading");
    setErrorDetails(null);

    try {
      // Step 1: Upload document
      const uploadRes = await uploadPdf(file);
      const patientId = uploadRes.patient_id || "PT-8821";

      // Step 2: Analyze historical reports & consolidate risk
      const analysisRes = await analyzePatient(patientId);
      setAnalysisData(analysisRes);
      setViewState("results");
    } catch (err: any) {
      console.error("Clinical pipeline error:", err);
      setErrorDetails({
        title: "Clinical Analysis Pipeline Interrupted",
        message: err.message || "Failed to parse document reports or generate risk model.",
        code: "ERR_CLINICAL_PIPELINE_FAILED"
      });
      setViewState("error");
    }
  };

  const handleReset = () => {
    setViewState("upload");
    setCurrentFile(null);
    setAnalysisData(null);
    setErrorDetails(null);
  };

  return (
    <div className="min-h-screen bg-[#f8f9fa] text-[#191c1d] flex flex-col font-sans selection:bg-[#00685f]/20 selection:text-[#00685f]">
      {/* Top Clinical Header */}
      <ClinicalHeader
        onReset={handleReset}
        showReset={viewState === "results" || viewState === "error"}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">
        <AnimatePresence mode="wait">
          {/* VIEW 1: Upload View */}
          {viewState === "upload" && (
            <motion.div
              key="upload"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="py-4 sm:py-8 space-y-6"
            >
              <div className="text-center max-w-2xl mx-auto space-y-2 mb-8">
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-[#00685f]/10 text-[#00685f]">
                  <HeartPulse className="w-3.5 h-3.5" />
                  <span>Cardiovascular Clinical Triage Engine</span>
                </div>
                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#191c1d] tracking-tight">
                  Consolidate Patient Cardiology Reports
                </h1>
                <p className="text-sm text-[#585e6c]">
                  Automated multi-encounter vital synthesis, consistent risk factor extraction, and rapid triage flag generation for physician review.
                </p>
              </div>

              <UploadCard
                onAnalyze={runAnalysisPipeline}
                onSelectPreset={() => {}}
                isLoading={false}
              />
            </motion.div>
          )}

          {/* VIEW 2: Loading State */}
          {viewState === "loading" && (
            <motion.div
              key="loading"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="py-12"
            >
              <LoadingState fileName={currentFile?.name} />
            </motion.div>
          )}

          {/* VIEW 3: Results View */}
          {viewState === "results" && analysisData && (
            <motion.div
              key="results"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="space-y-6"
            >
              {/* 1. Risk Flag Badge (Top) */}
              <RiskBadge
                risk={analysisData.risk}
                patientMeta={analysisData.patient_meta}
                onNewAnalysis={handleReset}
              />

              {/* 2. Side-by-Side: Factors Grid (left/main) + Factors Chart (right) on desktop */}
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
                <div className="lg:col-span-7">
                  <FactorsGrid profile={analysisData.final_profile} />
                </div>
                <div className="lg:col-span-5">
                  <FactorsChart
                    topFactors={analysisData.risk.top_3_factors}
                    riskLevel={analysisData.risk.risk_level}
                  />
                </div>
              </div>

              {/* 3. Evidence Accordion */}
              <EvidenceAccordion reports={analysisData.reports} />

              {/* 4. Summary for Doctor Review Card */}
              <ExplanationCard
                explanation={analysisData.explanation}
                riskLevel={analysisData.risk.risk_level}
              />
            </motion.div>
          )}

          {/* VIEW 4: Error State */}
          {viewState === "error" && (
            <motion.div
              key="error"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="py-12"
            >
              <ErrorState
                error={errorDetails}
                onRetry={() => currentFile && runAnalysisPipeline(currentFile)}
                onNewUpload={handleReset}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Persistent Clinical Disclaimer Footer */}
      <footer className="bg-white border-t border-[#e1e3e4] py-4 px-4 sm:px-6 lg:px-8 mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">
          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">
            <Info className="w-4 h-4 text-[#00685f] shrink-0" />
            <span>{CLINICAL_DISCLAIMER}</span>
          </div>

          <div className="flex items-center gap-4 text-[11px] text-[#585e6c]">
            <span className="flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Physician-in-the-Loop Triage Architecture
            </span>
            <span className="hidden sm:inline text-slate-300">•</span>
            <span>Version 2.4.0-triage</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
