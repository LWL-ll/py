import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface HeatmapPoint {
  month: string;
  row: number;
  temp: number | null;
}

export default function HeatmapChart() {
  const { selectedMonth, refreshKey } = useMonth();
  const [heatmapData, setHeatmapData] = useState<HeatmapPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const year = selectedMonth.split('-')[0];
    fetch(`/api/weather/heatmap/?year=${year}`)
      .then((res) => res.json())
      .then((json) => {
        if (json.code === 0) {
          setHeatmapData(json.data || []);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedMonth, refreshKey]);

  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];

  const getHeatColor = (temp: number | null) => {
    if (temp == null) return '#E8E8E6';
    if (temp < 15) return '#7FA3C1';
    if (temp < 20) return '#81B29A';
    if (temp < 25) return '#D4A373';
    return '#E07A5F';
  };

  // row 含义: 0=最低温, 1=P25, 2=中位数, 3=P75, 4=最高温
  const rowLabels = ['最低', 'P25', '中位', 'P75', '最高'];

  if (loading && heatmapData.length === 0) {
    return (
      <div className="w-full flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-[#8E8E93]" />
        <span className="ml-2 text-sm text-[#8E8E93]">加载热力图...</span>
      </div>
    );
  }

  if (heatmapData.length === 0) {
    return (
      <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-6 text-center text-sm text-[#8E8E93] shadow-sm">
        暂无热力图数据，请先爬取天气数据
      </div>
    );
  }

  return (
    <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
        <h3 className="text-lg font-semibold text-[#1C1C1E]">年度温度热力分布</h3>
      </div>
      <div className="bg-[#FAFAF8] rounded-xl p-6">
        <div className="grid grid-cols-12 gap-2 mb-4">
          {months.map((monthLabel) => (
            <div key={monthLabel} className="flex flex-col gap-1">
              {Array.from({ length: 5 }).map((_, rowIndex) => {
                const dataPoint = heatmapData.find(
                  (d) => d.month === monthLabel && d.row === rowIndex
                );
                return (
                  <div
                    key={`${monthLabel}-${rowIndex}`}
                    className="w-full aspect-square rounded-md transition-transform hover:scale-110 cursor-pointer"
                    style={{ backgroundColor: getHeatColor(dataPoint?.temp ?? null) }}
                    title={`${monthLabel} ${rowLabels[rowIndex]}: ${dataPoint?.temp ?? '-'}°C`}
                  ></div>
                );
              })}
              <span className="text-[10px] text-[#8E8E93] text-center mt-1">{monthLabel}</span>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-[#E8E8E6]">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#7FA3C1]"></div>
            <span className="text-xs text-[#6E6E73]">偏冷 (&lt;15°C)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#81B29A]"></div>
            <span className="text-xs text-[#6E6E73]">舒适 (15-20°C)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#D4A373]"></div>
            <span className="text-xs text-[#6E6E73]">温暖 (20-25°C)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#E07A5F]"></div>
            <span className="text-xs text-[#6E6E73]">炎热 (&gt;25°C)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
