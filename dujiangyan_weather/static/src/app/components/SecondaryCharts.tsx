import { useState, useEffect } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar,
} from 'recharts';
import { Loader2 } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface RainMonth {
  month: string;
  days: number;
}

interface ClimateScore {
  category: string;
  value: number;
}

export default function SecondaryCharts() {
  const { selectedMonth, refreshKey } = useMonth();
  const [rainData, setRainData] = useState<RainMonth[]>([]);
  const [climateData, setClimateData] = useState<ClimateScore[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    const year = selectedMonth.split('-')[0];
    const month = selectedMonth.split('-')[1];

    Promise.all([
      fetch(`/api/weather/monthly/?year=${year}`).then((r) => r.json()),
      fetch(`/api/weather/climate-score/?year=${year}&month=${month}`).then((r) => r.json()),
    ])
      .then(([monthlyJson, scoreJson]) => {
        // 降雨天数
        if (monthlyJson.code === 0) {
          const sorted = [...(monthlyJson.data || [])].sort(
            (a: { month: number }, b: { month: number }) => a.month - b.month
          );
          setRainData(
            sorted.map((d: { month: number; rainy_days: number }) => ({
              month: `${d.month}月`,
              days: d.rainy_days ?? 0,
            }))
          );
        }
        // 气候评分
        if (scoreJson.code === 0 && scoreJson.data?.length) {
          setClimateData(scoreJson.data);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedMonth, refreshKey]);

  if (loading && rainData.length === 0) {
    return (
      <div className="w-full flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-[#8E8E93]" />
        <span className="ml-2 text-sm text-[#8E8E93]">加载图表数据...</span>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col lg:flex-row gap-6">
      {/* Left Card - Monthly Rain Days */}
      <div className="flex-1 bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">月度降雨天数统计</h3>
        </div>
        <div className="bg-[#FAFAF8] rounded-xl p-4 h-[240px]">
          {rainData.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-[#8E8E93]">
              暂无降雨数据
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={rainData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F5F5F0" vertical={false} />
                <XAxis dataKey="month" stroke="#8E8E93" style={{ fontSize: '11px' }} />
                <YAxis stroke="#8E8E93" style={{ fontSize: '11px' }} />
                <Tooltip />
                <defs>
                  <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#4A6FA5" />
                    <stop offset="100%" stopColor="#7FA3C1" />
                  </linearGradient>
                </defs>
                <Bar dataKey="days" fill="url(#barGradient)" radius={[6, 6, 0, 0]} name="降雨天数" />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Right Card - Climate Score Radar */}
      <div className="flex-1 bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">气候综合评分</h3>
        </div>
        <div className="bg-[#FAFAF8] rounded-xl p-4 h-[240px] flex items-center justify-center">
          {climateData.length === 0 ? (
            <div className="text-sm text-[#8E8E93]">暂无评分数据</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={climateData}>
                <PolarGrid stroke="#E8E8E6" />
                <PolarAngleAxis dataKey="category" stroke="#8E8E93" style={{ fontSize: '11px' }} />
                <PolarRadiusAxis stroke="#8E8E93" style={{ fontSize: '10px' }} />
                <Radar
                  name="评分"
                  dataKey="value"
                  stroke="#4A6FA5"
                  fill="#4A6FA5"
                  fillOpacity={0.15}
                  strokeWidth={2}
                />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
