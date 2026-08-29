
import React, { Suspense, lazy } from "react";
import {
  Heart,
  Activity,
  Flame,
  Scale,
  User,
  Cigarette,
  FileSpreadsheet,
  AlertTriangle,
} from "lucide-react";

import { FinalProfile } from "../types/clinical";
// Lazy-load AnimatedList component
const AnimatedList = lazy(() => import("./ui/animated-list"));

interface FactorsGridProps {
  profile: FinalProfile;
}

export const FactorsGrid: React.FC<FactorsGridProps> = ({ profile }) => {
  const highFactors = profile.consistent_high_factors || [];

  // ------------------------------------------------------------
  // CHECK WHETHER A FACTOR WAS ACTUALLY REPORTED
  // ------------------------------------------------------------

  const isReported = (value: unknown): boolean => {
    if (value === null || value === undefined) {
      return false;
    }

    if (typeof value === "string") {
      return value.trim() !== "";
    }

    return true;
  };

  // ------------------------------------------------------------
  // CHECK CONSISTENTLY HIGH FACTORS
  // ------------------------------------------------------------

  const isFactorHigh = (key: string) => {
    return highFactors.some((f) => {
      const fLower = f.toLowerCase();
      const kLower = key.toLowerCase();

      return (
        fLower === kLower ||
        fLower.includes(kLower) ||
        kLower.includes(fLower)
      );
    });
  };

  // ------------------------------------------------------------
  // SAFE DISPLAY HELPERS
  // ------------------------------------------------------------

  const displayValue = (
    value: unknown,
    fallback = "Not reported"
  ): string => {
    return isReported(value) ? String(value) : fallback;
  };

  // ------------------------------------------------------------
  // FACTOR CARDS
  // ------------------------------------------------------------

  const factorCards = [
    {
      id: "factor-bp",
      key: "bp",
      label: "Blood Pressure",
      value: displayValue(profile.bp),
      unit: isReported(profile.bp) ? "mmHg" : "",
      category: "Cardiovascular",
      icon: Heart,

      isHigh:
        isReported(profile.bp) &&
        (isFactorHigh("blood pressure") ||
          isFactorHigh("systolic") ||
          isFactorHigh("bp")),

      threshold: isReported(profile.bp)
        ? "Target < 120/80"
        : "Not reported",
    },

    {
      id: "factor-cholesterol",
      key: "cholesterol",
      label: "Total Cholesterol",
      value: displayValue(profile.cholesterol),
      unit: "",

      category: "Lipid Panel",
      icon: Activity,

      isHigh:
        isReported(profile.cholesterol) &&
        (isFactorHigh("cholesterol") ||
          isFactorHigh("lipid")),

      threshold: isReported(profile.cholesterol)
        ? "Target: Normal"
        : "Not reported",
    },

    {
      id: "factor-glucose",
      key: "glucose",
      label: "Fasting Glucose",
      value: displayValue(profile.glucose),
      unit: "",

      category: "Metabolic",
      icon: Flame,

      isHigh:
        isReported(profile.glucose) &&
        (isFactorHigh("glucose") ||
          isFactorHigh("gluc")),

      threshold: isReported(profile.glucose)
        ? "Target: Normal"
        : "Not reported",
    },

    {
      id: "factor-bmi",
      key: "bmi",
      label: "Body Mass Index",

      value: isReported(profile.bmi)
        ? String(profile.bmi)
        : "Not reported",

      unit: isReported(profile.bmi)
        ? "kg/m²"
        : "",

      category: "Anthropometric",
      icon: Scale,

      isHigh:
        isReported(profile.bmi) &&
        (isFactorHigh("body mass index") ||
          isFactorHigh("bmi")),

      threshold: isReported(profile.bmi)
        ? "Target 18.5–24.9"
        : "Not reported",
    },

    {
      id: "factor-age",
      key: "age",
      label: "Patient Age",

      value: isReported(profile.age)
        ? String(profile.age)
        : "Not reported",

      unit: isReported(profile.age)
        ? "years"
        : "",

      category: "Demographic",
      icon: User,

      isHigh:
        isReported(profile.age) &&
        isFactorHigh("age"),

      threshold: isReported(profile.age)
        ? "Non-modifiable"
        : "Not reported",
    },

    {
      id: "factor-smoking",
      key: "smoking",
      label: "Smoking Status",

      value: isReported(profile.smoking)
        ? String(profile.smoking)
        : "Not reported",

      unit: "",

      category: "Behavioral",
      icon: Cigarette,

      isHigh:
        isReported(profile.smoking) &&
        profile.smoking?.toLowerCase() === "yes",

      threshold: isReported(profile.smoking)
        ? "Cessation target"
        : "Not reported",
    },

    {
      id: "factor-history",
      key: "history",
      label: "Family CVD History",

      value: isReported(profile.history)
        ? (
            profile.history?.toLowerCase() === "yes"
              ? "Positive"
              : "Negative"
          )
        : "Not reported",

      unit: "",

      category: "Genetic",
      icon: FileSpreadsheet,

      isHigh:
        isReported(profile.history) &&
        (
          profile.history?.toLowerCase() === "yes" ||
          isFactorHigh("family") ||
          isFactorHigh("history")
        ),

      threshold: isReported(profile.history)
        ? "1st degree CAD"
        : "Not reported",
    },
  ];

  // ------------------------------------------------------------
  // RENDER CARD
  // ------------------------------------------------------------

  const renderCard = (
    card: typeof factorCards[0]
  ) => {
    const IconComponent = card.icon;

    return (
      <div
        key={card.id}
        id={card.id}
        className={`p-3.5 rounded-xl border transition-all ${
          card.isHigh
            ? "border-rose-300/80 bg-rose-50/40 shadow-xs"
            : "border-[#e1e3e4] bg-[#f8f9fa]/70 hover:bg-[#f8f9fa]"
        }`}
      >
        <div className="flex items-start justify-between">
          <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider">
            {card.label}
          </span>

          <div
            className={`w-6 h-6 rounded-md flex items-center justify-center ${
              card.isHigh
                ? "bg-rose-100 text-rose-700"
                : "bg-slate-200/80 text-slate-600"
            }`}
          >
            <IconComponent className="w-3.5 h-3.5" />
          </div>
        </div>

        {/* Primary Metric Value */}
        <div className="mt-2 flex items-baseline gap-1.5">
          <span
            className={`text-xl font-bold tracking-tight ${
              card.isHigh
                ? "text-rose-950"
                : "text-[#191c1d]"
            }`}
          >
            {card.value}
          </span>

          {card.unit && (
            <span className="text-xs text-slate-500 font-medium">
              {card.unit}
            </span>
          )}
        </div>

        {/* Threshold / Status */}
        <div className="mt-2.5">
          {card.isHigh ? (
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
              <AlertTriangle className="w-3 h-3 text-rose-600 shrink-0" />

              <span>
                Consistently high across reports
              </span>
            </div>
          ) : (
            <div className="text-[10px] text-slate-400 font-medium">
              {card.threshold}
            </div>
          )}
        </div>
      </div>
    );
  };

  // ------------------------------------------------------------
  // UI
  // ------------------------------------------------------------

  return (
    <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5 sm:p-6 shadow-[0_4px_20px_rgba(0,0,0,0.04)] h-full flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-4 pb-3 border-b border-[#e1e3e4]">
          <div>
            <h3 className="text-base font-bold text-[#191c1d] flex items-center gap-2">
              <Activity className="w-4 h-4 text-[#00685f]" />

              Consolidated Clinical Factors
            </h3>

            <p className="text-xs text-[#585e6c]">
              Synthesized latest parameters from historical report extraction
            </p>
          </div>

          <span className="text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
            {factorCards.length} Parameters
          </span>
        </div>

        <Suspense
          fallback={
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {factorCards.map((card) =>
                renderCard(card)
              )}
            </div>
          }
        >
          <AnimatedList
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
            staggerDelay={0.05}
            duration={0.22}
            yOffset={8}
          >
            {factorCards.map((card) =>
              renderCard(card)
            )}
          </AnimatedList>
        </Suspense>
      </div>

      <div className="mt-4 pt-3 border-t border-[#e1e3e4] flex items-center justify-between text-[11px] text-slate-500">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-rose-500 inline-block"></span>

          Highlighted = Consistently elevated in multi-encounter tracking
        </span>

        <span className="text-slate-400">
          Values standardized
        </span>
      </div>
    </div>
  );
};
