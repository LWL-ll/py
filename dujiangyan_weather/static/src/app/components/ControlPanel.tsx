import { CloudDownload, BarChart3, Loader2 } from 'lucide-react';
import { useState } from 'react';

export default function ControlPanel() {
  const [isLoading, setIsLoading] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState('2025-06');

  const handleFetch = () => {
    setIsLoading(true);
    setTimeout(() => setIsLoading(false), 2000);
  };

  return (
    <div className="w-full bg-white rounded-xl shadow-[0_4px_6px_rgba(0,0,0,0.05)] p-6">
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex flex-col gap-2">
          <label className="text-sm text-slate-600">选择月份</label>
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="w-40 h-10 px-3 border border-slate-300 rounded-lg bg-white text-slate-900"
          >
            <option value="2025-06">2025-06</option>
            <option value="2025-05">2025-05</option>
            <option value="2025-04">2025-04</option>
          </select>
        </div>

        <button
          onClick={handleFetch}
          className="flex items-center gap-2 h-10 px-6 bg-[#10B981] text-white rounded-lg hover:bg-[#059669] transition-colors"
        >
          <CloudDownload className="w-4 h-4" />
          <span>一键爬取</span>
        </button>

        <button className="flex items-center gap-2 h-10 px-6 bg-[#0EA5E9] text-white rounded-lg hover:bg-[#0284C7] transition-colors">
          <BarChart3 className="w-4 h-4" />
          <span>开始分析</span>
        </button>

        {isLoading && (
          <div className="flex items-center gap-2 text-slate-600">
            <Loader2 className="w-4 h-4 animate-spin" />
            <span className="text-sm">数据爬取中，请稍候...</span>
          </div>
        )}
      </div>
    </div>
  );
}
