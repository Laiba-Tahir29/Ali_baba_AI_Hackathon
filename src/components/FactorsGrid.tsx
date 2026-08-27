import React, { Suspense, lazy } from "react";
import { Heart, Activity, Flame, Scale, User, Cigarette, FileSpreadsheet, AlertTriangle } from "lucide-react";
import { FinalProfile } from "../types/clinical";

// Lazy-load AnimatedList component per performance guardrails
const AnimatedList = lazy(() => import("./ui/animated-list"));

interface FactorsGridProps {
  profile: FinalProfile;
}

export const FactorsGrid: React.FC<FactorsGridProps> = ({ profile }) => {
  const highFactors = profile.consistent_high_factors || [];

  const isFactorHigh = (key: string) => {
    return highFactors.some((f) => {
      const fLower = f.toLowerCase();
      const kLower = key.toLowerCase();
      return fLower === kLower || fLower.includes(kLower) || kLower.includes(fLower);
    });
  };

  const factorCards = [
    {
      id: "factor-bp",
      key: "bp",
      label: "Blood Pressure",
      value: profile.bp,
      unit: "mmHg",
      category: "Cardiovascular",
      icon: Heart,
      isHigh: isFactorHigh("blood pressure") || isFactorHigh("systolic") || isFactorHigh("bp"),
      threshold: "Target < 120/80"
    },
    {
      id: "factor-cholesterol",
      key: "cholesterol",
      label: "Total Cholesterol",
      value: profile.cholesterol,
      unit: "",
      category: "Lipid Panel",
      icon: Activity,
      isHigh: isFactorHigh("cholesterol") || isFactorHigh("lipid"),
      threshold: "Target: Normal"
    },
    {
      id: "factor-glucose",
      key: "glucose",
      label: "Fasting Glucose",
      value: profile.glucose,
      unit: "",
      category: "Metabolic",
      icon: Flame,
      isHigh: isFactorHigh("glucose") || isFactorHigh("gluc"),
      threshold: "Target: Normal"
    },
    {
      id: "factor-bmi",
      key: "bmi",
      label: "Body Mass Index",
      value: profile.bmi ? profile.bmi.toString() : "—",
      unit: "kg/m²",
      category: "Anthropometric",
      icon: Scale,
      isHigh: isFactorHigh("body mass index") || isFactorHigh("bmi"),
      threshold: "Target 18.5–24.9"
    },
    {
      id: "factor-age",
      key: "age",
      label: "Patient Age",
      value: profile.age ? `${profile.age}` : "—",
      unit: "years",
      category: "Demographic",
      icon: User,
      isHigh: isFactorHigh("age"),
      threshold: "Non-modifiable"
    },
    {
      id: "factor-smoking",
      key: "smoking",
      label: "Smoking Status",
      value: profile.smoking ? profile.smoking.charAt(0).toUpperCase() + profile.smoking.slice(1) : "No",
      unit: "",
      category: "Behavioral",
      icon: Cigarette,
      isHigh: profile.smoking?.toLowerCase() === "yes" || isFactorHigh("smoking"),
      threshold: "Cessation target"
    },
    {
      id: "factor-history",
      key: "history",
      label: "Family CVD History",
      value: profile.history ? (profile.history.toLowerCase() === "yes" ? "Positive" : "Negative") : "Negative",
      unit: "",
      category: "Genetic",
      icon: FileSpreadsheet,
      isHigh: profile.history?.toLowerCase() === "yes" || isFactorHigh("family") || isFactorHigh("history"),
      threshold: "1st degree CAD"
    }
  ];

  const renderCard = (card: typeof factorCards[0]) => {
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
          <span className={`text-xl font-bold tracking-tight ${card.isHigh ? "text-rose-950" : "text-[#191c1d]"}`}>
            {card.value}
          </span>
          {card.unit && (
            <span className="text-xs text-slate-500 font-medium">
              {card.unit}
            </span>
          )}
        </div>

        {/* Threshold or High Indicator */}
        <div className="mt-2.5">
          {card.isHigh ? (
            <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200">
              <AlertTriangle className="w-3 h-3 text-rose-600 shrink-0" />
              <span>Consistently high across reports</span>
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

        {/* Factors Grid wrapped with React Bits AnimatedList for fast 50ms stagger entrance */}
        <Suspense
          fallback={
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
              {factorCards.map((card) => renderCard(card))}
            </div>
          }
        >
          <AnimatedList
            className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3"
            staggerDelay={0.05} // 50ms per item stagger
            duration={0.22}
            yOffset={8}
          >
            {factorCards.map((card) => renderCard(card))}
          </AnimatedList>
        </Suspense>
      </div>

      <div className="mt-4 pt-3 border-t border-[#e1e3e4] flex items-center justify-between text-[11px] text-slate-500">
        <span className="flex items-center gap-1">
          <span className="w-2 h-2 rounded-full bg-rose-500 inline-block"></span>
          Highlighted = Consistently elevated in multi-encounter tracking
        </span>
        <span className="text-slate-400">Values standardized</span>
      </div>
    </div>
  );
};
