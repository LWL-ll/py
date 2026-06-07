import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';
import { Loader2 } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface TempPoint {
  month: string;
  avgMax: number | null;
  avgMin: number | null;
}

interface PieSlice {
  name: string;
  value: number;
  color: string;
}

export default function PrimaryCharts() {
  const { selectedMonth, refreshKey } = useMonth();
  const [tempData, setTempData] = useState<TempPoint[]>([]);
  const [pieData, setPieData] = useState<PieSlice[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalDays, setTotalDays] = useState(0);

  useEffect(() => {
    setLoading(true);
    const year = selectedMonth.split('-')[0];

    // 并行请求：温度趋势 + 天气分布
    Promise.all([
      fetch(`/api/weather/monthly/?year=${year}`).then((r) => r.json()),
      fetch(`/api/weather/distribution/?year=${year}`).then((r) => r.json()),
    ])
      .then(([monthlyJson, distJson]) => {
        // 温度趋势
        if (monthlyJson.code === 0) {
          const sorted = [...(monthlyJson.data || [])].sort(
            (a: { month: number }, b: { month: number }) => a.month - b.month
          );
          setTempData(
            sorted.map((d: { month: number; avg_max_temp: number | null; avg_min_temp: number | null }) => ({
              month: `${d.month}月`,
              avgMax: d.avg_max_temp,
              avgMin: d.avg_min_temp,
            }))
          );
        }
        // 天气分布（仅取当前选中月份的数据）
        if (distJson.code === 0) {
          const dist: PieSlice[] = distJson.data || [];
          setPieData(dist);
          const sum = dist.reduce((acc, d) => acc + d.value, 0);
          setTotalDays(sum);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedMonth, refreshKey]);

  if (loading && tempData.length === 0) {
    return (
      <div className="w-full flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-[#8E8E93]" />
        <span className="ml-2 text-sm text-[#8E8E93]">加载图表数据...</span>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-col lg:flex-row gap-6">
      {/* Left Chart Card - Temperature Trend */}
      <div className="flex-[2] bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">月度温度变化趋势</h3>
        </div>
        <div className="bg-[#FAFAF8] rounded-xl p-4 h-[320px]">
          {tempData.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-[#8E8E93]">
              暂无温度数据
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={tempData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E8E8E6" vertical={false} />
                <XAxis dataKey="month" stroke="#8E8E93" style={{ fontSize: '12px' }} />
                <YAxis stroke="#8E8E93" style={{ fontSize: '12px' }} unit="℃" />
                <Tooltip />
                <Line
                  type="monotone"
                  dataKey="avgMax"
                  stroke="#E07A5F"
                  strokeWidth={3}
                  dot={{ fill: '#E07A5F', r: 4 }}
                  name="最高温"
                  connectNulls
                />
                <Line
                  type="monotone"
                  dataKey="avgMin"
                  stroke="#7FA3C1"
                  strokeWidth={3}
                  dot={{ fill: '#7FA3C1', r: 4 }}
                  name="最低温"
                  connectNulls
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Right Chart Card - Weather Distribution */}
      <div className="flex-1 bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">天气状况分布</h3>
        </div>
        <div className="flex flex-col items-center gap-4">
          {pieData.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-sm text-[#8E8E93]">
              暂无分布数据
            </div>
          ) : (
            <>
              <div className="relative w-[200px] h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={90}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                  </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-lg font-bold text-[#1C1C1E]">{totalDays}天</span>
                </div>
              </div>
              <div className="flex flex-col gap-2 w-full">
                {pieData.map((item) => (
                  <div key={item.name} className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></div>
                    <span className="text-[13px] text-[#6E6E73]">{item.name}</span>
                    <span className="ml-auto text-[13px] font-medium text-[#1C1C1E]">{item.value}</span>
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
