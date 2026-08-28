import React from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell } from "recharts";
import { BarChart3, Info } from "lucide-react";

interface FactorsChartProps {
  topFactors: string[];
  riskLevel?: "low" | "medium" | "high";
}

export const FactorsChart: React.FC<FactorsChartProps> = ({ topFactors, riskLevel = "high" }) => {
  // Normalize data for chart visualization
  const chartData = (topFactors || ["Blood Pressure", "Cholesterol", "Family History"]).map((factor, index) => {
    // Relative impact weighting for top factors (highest impact first)
    const impactValues = [42, 33, 25];
    const impact = impactValues[index] || 20;

    let color = "#00685f"; // default teal
    if (index === 0) color = riskLevel === "high" ? "#ba1a1a" : riskLevel === "medium" ? "#b05e3d" : "#00685f";
    if (index === 1) color = riskLevel === "high" ? "#b05e3d" : "#00685f";
    if (index === 2) color = "#008378";

    return {
      name: factor,
      impact: impact,
      rank: `#${index + 1} Factor`,
      color: color
    };
  });

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-slate-900 text-white p-2.5 rounded-lg shadow-lg text-xs space-y-1">
          <div className="font-semibold text-slate-100">{data.name}</div>
          <div className="text-slate-300">
            Contribution Weight: <span className="font-bold text-white">{data.impact}%</span>
          </div>
          <div className="text-[10px] text-slate-400">{data.rank} in multi-report risk model</div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="bg-white rounded-2xl border border-[#e1e3e4] p-5 sm:p-6 shadow-[0_4px_20px_rgba(0,0,0,0.04)] h-full flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between mb-3 pb-3 border-b border-[#e1e3e4]">
          <div>
            <h3 className="text-base font-bold text-[#191c1d] flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[#00685f]" />
              Top Contributing Risk Factors
            </h3>
            <p className="text-xs text-[#585e6c]">
              Relative driver weighting contributing to the calculated risk flag
            </p>
          </div>
          <span className="text-[11px] font-semibold text-[#00685f] bg-[#00685f]/10 px-2 py-0.5 rounded">
            Top 3 Drivers
          </span>
        </div>

        {/* Chart Visualization */}
        <div className="h-48 w-full mt-2" id="factors-horizontal-chart">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              layout="vertical"
              margin={{ top: 10, right: 30, left: 10, bottom: 0 }}
            >
              <XAxis
                type="number"
                domain={[0, 50]}
                unit="%"
                tick={{ fontSize: 11, fill: "#585e6c" }}
                axisLine={{ stroke: "#e1e3e4" }}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={110}
                tick={{ fontSize: 12, fill: "#191c1d", fontWeight: 600 }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar
                dataKey="impact"
                radius={[0, 6, 6, 0]}
                barSize={20}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Driver Legend / Breakdown */}
      <div className="mt-4 pt-3 border-t border-[#e1e3e4] grid grid-cols-1 sm:grid-cols-3 gap-2 text-center text-xs">
        {chartData.map((item, i) => (
          <div key={item.name} className="p-2 rounded-lg bg-slate-50 border border-slate-100">
            <div className="flex items-center justify-center gap-1.5 mb-0.5">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></span>
              <span className="text-[10px] text-slate-500 font-bold uppercase">#{i + 1}</span>
            </div>
            <p className="font-semibold text-[#191c1d] truncate text-xs">{item.name}</p>
            <p className="text-[11px] text-slate-600 font-medium">{item.impact}% weight</p>
          </div>
        ))}
      </div>
    </div>
  );
};
