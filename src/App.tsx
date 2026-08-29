
import React, { useState } from "react";
import {
  AnimatePresence,
  motion,
  useReducedMotion,
  Variants,
} from "framer-motion";

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

import {
  AnalysisResponse,
  ViewState,
  ErrorDetails,
} from "./types/clinical";

import {
  ShieldCheck,
  Info,
  HeartPulse,
} from "lucide-react";

export default function App() {
  const [viewState, setViewState] =
    useState<ViewState>("upload");

  const [currentFile, setCurrentFile] =
    useState<File | null>(null);

  const [analysisData, setAnalysisData] =
    useState<AnalysisResponse | null>(null);

  const [errorDetails, setErrorDetails] =
    useState<ErrorDetails | null>(null);

  const shouldReduceMotion = useReducedMotion();

  // ============================================================
  // PAGE TRANSITION
  // ============================================================

  const pageVariants: Variants = {
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

  // ============================================================
  // RUN ANALYSIS PIPELINE
  // ============================================================

  const runAnalysisPipeline = async (file: File) => {
    setCurrentFile(file);
    setViewState("loading");
    setErrorDetails(null);

    try {
      // Step 1: Upload PDF
      const uploadRes = await uploadPdf(file);

      const patientId = uploadRes.patient_id;

      // Step 2: Analyze patient reports
      const analysisRes = await analyzePatient(patientId);

      setAnalysisData(analysisRes);
      setViewState("results");
    } catch (err: any) {
      console.error(
        "Clinical pipeline error:",
        err
      );

      setErrorDetails({
        title:
          "Clinical Analysis Pipeline Interrupted",

        message:
          err.message ||
          "Failed to parse document reports or generate risk model.",

        code:
          "ERR_CLINICAL_PIPELINE_FAILED",
      });

      setViewState("error");
    }
  };

  // ============================================================
  // RESET
  // ============================================================

  const handleReset = () => {
    setViewState("upload");
    setCurrentFile(null);
    setAnalysisData(null);
    setErrorDetails(null);
  };

  // ============================================================
  // RENDER
  // ============================================================

  return (
    <div className="min-h-screen  bg-[#f2f7f6] text-[#191c1d] flex flex-col font-sans selection:bg-[#00685f]/20 selection:text-[#00685f]">

      {/* ======================================================
          TOP CLINICAL HEADER
      ====================================================== */}

      <ClinicalHeader
        onReset={handleReset}
        showReset={
          viewState === "results" ||
          viewState === "error"
        }
      />

      {/* ======================================================
          MAIN CONTENT
      ====================================================== */}

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">

        <AnimatePresence mode="wait">

          {/* ==================================================
              VIEW 1: UPLOAD
          ================================================== */}

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

                  <span>
                    Cardiovascular Clinical Triage Engine
                  </span>
                </div>

                <h1 className="text-2xl sm:text-3xl font-extrabold text-[#191c1d] tracking-tight">
                  Consolidate Patient Cardiology Reports
                </h1>

                <p className="text-sm text-[#585e6c]">
                  Automated multi-encounter vital synthesis,
                  consistent risk factor extraction, and rapid
                  triage flag generation for physician review.
                </p>

              </div>

              {/* UPDATED UPLOAD CARD */}
              <UploadCard
                onAnalyze={runAnalysisPipeline}
                isLoading={false}
              />

            </motion.div>
          )}

          {/* ==================================================
              VIEW 2: LOADING
          ================================================== */}

          {viewState === "loading" && (
            <motion.div
              key="loading"
              variants={pageVariants}
              initial="initial"
              animate="animate"
              exit="exit"
              className="py-12"
            >
              <LoadingState
                fileName={currentFile?.name}
              />
            </motion.div>
          )}

          {/* ==================================================
              VIEW 3: RESULTS
          ================================================== */}

          {viewState === "results" &&
            analysisData && (

              analysisData.status === "insufficient_data"

                ? (

                  /* ==================================================
                     INSUFFICIENT DATA
                  ================================================== */

                  <motion.div
                    key="insufficient-data"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="space-y-6"
                  >

                    {/* WARNING */}

                    <div className="rounded-2xl border border-amber-200 bg-amber-50 p-6 shadow-sm">

                      <h2 className="text-xl font-bold text-amber-900">
                        Insufficient data for a reliable score
                      </h2>

                      <p className="mt-2 text-sm text-amber-800">
                        {analysisData.message ||
                          "A reliable cardiovascular risk score could not be computed."}
                      </p>

                      {analysisData.missing_fields &&
                        analysisData.missing_fields.length > 0 && (

                          <div className="mt-4">

                            <p className="text-sm font-semibold text-amber-900">
                              Missing required fields:
                            </p>

                            <ul className="mt-2 list-disc list-inside text-sm text-amber-800">

                              {analysisData.missing_fields.map(
                                (field) => (
                                  <li key={field}>
                                    {field}
                                  </li>
                                )
                              )}

                            </ul>

                          </div>
                        )}

                    </div>

                    {/* CONSOLIDATED FACTORS */}

                    <FactorsGrid
                      profile={
                        analysisData.final_profile
                      }
                    />

                    {/* HISTORICAL EVIDENCE */}

                    <EvidenceAccordion
                      reports={
                        analysisData.reports || []
                      }
                    />

                    {/* GEMINI EXPLANATION */}

                    {analysisData.explanation && (
                      <ExplanationCard
                        explanation={
                          analysisData.explanation
                        }
                        riskLevel={undefined}
                      />
                    )}

                  </motion.div>

                )

                : (

                  /* ==================================================
                     NORMAL RESULTS
                  ================================================== */

                  <motion.div
                    key="results"
                    variants={pageVariants}
                    initial="initial"
                    animate="animate"
                    exit="exit"
                    className="space-y-6"
                  >

                    {/* IMPUTED FIELDS */}

                    {analysisData.imputed_fields &&
                      analysisData.imputed_fields.length > 0 && (

                        <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-800">

                          Some values were estimated:{" "}

                          {analysisData.imputed_fields.join(
                            ", "
                          )}

                          .

                        </div>
                      )}

                    {/* RISK BADGE */}

                    {analysisData.risk && (
                      <RiskBadge
                        risk={
                          analysisData.risk
                        }
                        patientMeta={
                          analysisData.patient_meta
                        }
                        onNewAnalysis={
                          handleReset
                        }
                      />
                    )}

                    {/* FACTORS + CHART */}

                    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">

                      <div className="lg:col-span-7">

                        <FactorsGrid
                          profile={
                            analysisData.final_profile
                          }
                        />

                      </div>

                      <div className="lg:col-span-5">

                        {analysisData.risk && (
                          <FactorsChart
                            topFactors={
                              analysisData.risk
                                .top_3_factors ||
                              analysisData.risk
                                .top_factors ||
                              []
                            }

                            riskLevel={
                              analysisData.risk
                                .risk_level ||
                              "low"
                            }
                          />
                        )}

                      </div>

                    </div>

                    {/* HISTORICAL EVIDENCE */}

                    <EvidenceAccordion
                      reports={
                        analysisData.reports || []
                      }
                    />

                    {/* GEMINI SUMMARY */}

                    {analysisData.explanation && (
                      <ExplanationCard
                        explanation={
                          analysisData.explanation
                        }
                        riskLevel={
                          analysisData.risk
                            ?.risk_level ||
                          "low"
                        }
                      />
                    )}

                  </motion.div>
                )
            )}

          {/* ==================================================
              VIEW 4: ERROR
          ================================================== */}

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

                onRetry={() =>
                  currentFile &&
                  runAnalysisPipeline(
                    currentFile
                  )
                }

                onNewUpload={
                  handleReset
                }
              />

            </motion.div>
          )}

        </AnimatePresence>

      </main>

      {/* ======================================================
          PERSISTENT CLINICAL DISCLAIMER FOOTER
      ====================================================== */}

      <footer className="bg-white border-t border-[#e1e3e4] py-4 px-4 sm:px-6 lg:px-8 mt-auto">

        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-3 text-center sm:text-left">

          <div className="flex items-center gap-2 text-xs font-semibold text-slate-700">

            <Info className="w-4 h-4 text-[#00685f] shrink-0" />

            <span>
              {CLINICAL_DISCLAIMER}
            </span>

          </div>

          <div className="flex items-center gap-4 text-[11px] text-[#585e6c]">

            <span className="flex items-center gap-1">

              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />

              Physician-in-the-Loop Triage Architecture

            </span>

            <span className="hidden sm:inline text-slate-300">
              •
            </span>

            <span>
              Version 2.4.0-triage
            </span>

          </div>

        </div>

      </footer>

    </div>
  );
}

