import React, { useState, Suspense, lazy } from "react";
import { ChevronDown, ChevronUp, FileText, Calendar, Building2, User, Quote, CheckCircle2 } from "lucide-react";
import { ReportItem } from "../types/clinical";

// Lazy-load AnimatedList component per performance guardrails
const AnimatedList = lazy(() => import("./ui/animated-list"));

interface EvidenceAccordionProps {
  reports: ReportItem[];
}

export const EvidenceAccordion: React.FC<EvidenceAccordionProps> = ({ reports }) => {
  // By default, open all or the first item
  const [openIndexes, setOpenIndexes] = useState<number[]>([0, 1, 2]);

  const toggleIndex = (index: number) => {
    setOpenIndexes((prev) =>
      prev.includes(index) ? prev.filter((i) => i !== index) : [...prev, index]
    );
  };

  const handleExpandAll = () => {
    setOpenIndexes(reports.map((_, i) => i));
  };

  const handleCollapseAll = () => {
    setOpenIndexes([]);
  };

  const renderReportItem = (report: ReportItem, idx: number) => {
    const isOpen = openIndexes.includes(idx);

    return (
      <div
        key={idx}
        className={`rounded-xl border transition-all duration-200 overflow-hidden ${
          isOpen
            ? "border-[#00685f]/30 bg-slate-50/50 shadow-xs"
            : "border-[#e1e3e4] bg-white hover:border-slate-300"
        }`}
      >
        {/* Header Button */}
        <button
          type="button"
          onClick={() => toggleIndex(idx)}
          className="w-full px-4 py-3.5 flex items-center justify-between text-left cursor-pointer transition-colors"
          aria-expanded={isOpen}
        >
          <div className="flex items-center gap-2.5 flex-wrap">
            <span className="w-6 h-6 rounded-full bg-[#00685f]/10 text-[#00685f] text-xs font-bold flex items-center justify-center shrink-0">
              {idx + 1}
            </span>

            <span className="font-bold text-sm text-[#191c1d] flex items-center gap-1.5">
              <User className="w-3.5 h-3.5 text-slate-400" />
              {report.doctor}
            </span>

            <span className="text-slate-300 hidden sm:inline">—</span>

            <span className="text-xs font-medium text-slate-600 flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5 text-slate-400" />
              {report.clinic}
            </span>

            <span className="text-slate-300 hidden sm:inline">—</span>

            <span className="text-xs font-semibold text-[#00685f] bg-[#00685f]/5 px-2 py-0.5 rounded flex items-center gap-1">
              <Calendar className="w-3 h-3 text-[#00685f]" />
              {report.date}
            </span>
          </div>

          <div className="text-slate-400 pl-2">
            {isOpen ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>

        {/* Accordion Body: Clinical Quote */}
        {isOpen && (
          <div className="px-5 pb-4 pt-1">
            <div className="p-4 rounded-xl bg-white border border-slate-200 relative shadow-xs">
              <Quote className="w-5 h-5 text-[#00685f]/30 absolute top-3 right-3" />
              <p className="text-xs text-slate-700 leading-relaxed italic pr-6 font-serif">
                "{report.snippet}"
              </p>
              <div className="mt-2.5 flex items-center justify-between text-[11px] text-slate-400 border-t border-slate-100 pt-2 font-sans">
                <span className="flex items-center gap-1 text-emerald-700">
                  <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                  Verified OCR Extraction from encounter note
                </span>
                <span>Encounter #{idx + 1}</span>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5 sm:p-6 shadow-[0_4px_20px_rgba(0,0,0,0.04)] mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 mb-4 border-b border-[#e1e3e4]">
        <div>
          <h3 className="text-base font-bold text-[#191c1d] flex items-center gap-2">
            <FileText className="w-4 h-4 text-[#00685f]" />
            Historical Document Evidence & Encounter Snippets
          </h3>
          <p className="text-xs text-[#585e6c]">
            Direct excerpts extracted across {reports.length} clinical encounter records
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleExpandAll}
            className="text-xs font-semibold text-[#00685f] hover:underline px-2 py-1 rounded cursor-pointer"
          >
            Expand All
          </button>
          <span className="text-slate-300">|</span>
          <button
            type="button"
            onClick={handleCollapseAll}
            className="text-xs font-medium text-slate-500 hover:text-slate-800 px-2 py-1 rounded cursor-pointer"
          >
            Collapse All
          </button>
        </div>
      </div>

      {/* Accordion list wrapped with React Bits AnimatedList for fast 50ms stagger */}
      <Suspense
        fallback={
          <div className="space-y-3" id="evidence-accordion-list">
            {reports.map((report, idx) => renderReportItem(report, idx))}
          </div>
        }
      >
        <AnimatedList
          className="space-y-3"
          staggerDelay={0.05} // 50ms stagger per item
          duration={0.22}
          yOffset={8}
        >
          {reports.map((report, idx) => renderReportItem(report, idx))}
        </AnimatedList>
      </Suspense>
    </div>
  );
};
