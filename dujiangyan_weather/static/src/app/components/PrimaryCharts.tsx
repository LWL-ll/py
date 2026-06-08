import { useState, useEffect } from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, ReferenceLine,
} from 'recharts';
import { Loader2 } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface TrendPoint {
  label: string;
  avgMax: number | null;
  avgMin: number | null;
  type: 'history' | 'forecast';
}

interface PieSlice {
  name: string;
  value: number;
  color: string;
}

/** 自定义 Tooltip */
function CustomTooltip({ active, payload }: { active?: boolean; payload?: any[] }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-[#E8E8E6] rounded-xl px-4 py-2 shadow-lg">
      {payload.map((p: any, i: number) => (
        <p key={i} className="text-sm" style={{ color: p.color }}>
          {p.name}: {p.value}°C
        </p>
      ))}
    </div>
  );
}

export default function PrimaryCharts() {
  const { selectedMonth, refreshKey } = useMonth();
  const [trendData, setTrendData] = useState<TrendPoint[]>([]);
  const [pieData, setPieData] = useState<PieSlice[]>([]);
  const [loading, setLoading] = useState(true);
  const [totalDays, setTotalDays] = useState(0);
  // 找到历史与预报的分界点
  const [splitIndex, setSplitIndex] = useState(-1);

  useEffect(() => {
    setLoading(true);
    const year = selectedMonth.split('-')[0];

    Promise.all([
      fetch('/api/weather/temperature-trend/').then((r) => r.json()),
      fetch(`/api/weather/distribution/?year=${year}`).then((r) => r.json()),
    ])
      .then(([trendJson, distJson]) => {
        // 温度趋势：拼接历史 + 预报
        if (trendJson.code === 0) {
          const history = trendJson.data?.history || [];
          const forecast = trendJson.data?.forecast || [];
          const combined = [...history, ...forecast];
          setTrendData(combined);
          setSplitIndex(history.length > 0 ? history.length - 1 : -1);
        }
        // 天气分布
        if (distJson.code === 0) {
          const dist: PieSlice[] = distJson.data || [];
          setPieData(dist);
          setTotalDays(dist.reduce((acc, d) => acc + d.value, 0));
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedMonth, refreshKey]);

  if (loading && trendData.length === 0) {
    return (
      <div className="w-full flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-[#8E8E93]" />
        <span className="ml-2 text-sm text-[#8E8E93]">加载图表数据...</span>
      </div>
    );
  }

  // 分离历史与预报数据用于两条线
  const histMaxData = trendData.filter((d) => d.type === 'history').map((d) => ({
    label: d.label, value: d.avgMax,
  }));
  const histMinData = trendData.filter((d) => d.type === 'history').map((d) => ({
    label: d.label, value: d.avgMin,
  }));
  const fcMaxData = trendData.filter((d) => d.type === 'forecast').map((d) => ({
    label: d.label, value: d.avgMax,
  }));
  const fcMinData = trendData.filter((d) => d.type === 'forecast').map((d) => ({
    label: d.label, value: d.avgMin,
  }));

  // 需要完整 labels 给 XAxis
  const allLabels = trendData.map((d) => d.label);

  return (
    <div className="w-full flex flex-col lg:flex-row gap-6">
      {/* Left Chart - Temperature Trend (历史+预报) */}
      <div className="flex-[2] bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">温度趋势（历史 + 预报）</h3>
          <span className="ml-auto flex items-center gap-3 text-xs text-[#8E8E93]">
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-[#E07A5F] inline-block"></span> 历史
            </span>
            <span className="flex items-center gap-1">
              <span className="w-3 h-0.5 bg-[#E07A5F] inline-block border-dashed"></span> 预报
            </span>
          </span>
        </div>
        <div className="bg-[#FAFAF8] rounded-xl p-4 h-[320px]">
          {trendData.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-[#8E8E93]">暂无温度数据</div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E8E8E6" vertical={false} />
                <XAxis dataKey="label" stroke="#8E8E93" style={{ fontSize: '11px' }}
                  allowDuplicatedCategory={false} />
                <YAxis stroke="#8E8E93" style={{ fontSize: '12px' }} unit="°C" />
                <Tooltip content={<CustomTooltip />} />

                {/* 历史-最高温：实线 */}
                <Line data={histMaxData} type="monotone" dataKey="value"
                  stroke="#E07A5F" strokeWidth={3} dot={{ fill: '#E07A5F', r: 3 }}
                  name="历史最高温" connectNulls />
                {/* 历史-最低温：实线 */}
                <Line data={histMinData} type="monotone" dataKey="value"
                  stroke="#7FA3C1" strokeWidth={3} dot={{ fill: '#7FA3C1', r: 3 }}
                  name="历史最低温" connectNulls />

                {/* 预报-最高温：虚线 */}
                <Line data={fcMaxData} type="monotone" dataKey="value"
                  stroke="#E07A5F" strokeWidth={2.5} dot={{ fill: '#E07A5F', r: 3 }}
                  strokeDasharray="6 3" name="预报最高温" connectNulls />
                {/* 预报-最低温：虚线 */}
                <Line data={fcMinData} type="monotone" dataKey="value"
                  stroke="#7FA3C1" strokeWidth={2.5} dot={{ fill: '#7FA3C1', r: 3 }}
                  strokeDasharray="6 3" name="预报最低温" connectNulls />

                {/* 历史/预报分界线 */}
                {splitIndex >= 0 && (
                  <ReferenceLine x={allLabels[splitIndex]} stroke="#8E8E93" strokeDasharray="4 4"
                    strokeWidth={1} label={{ value: '← 历史 | 预报 →', position: 'top',
                    style: { fontSize: '10px', fill: '#8E8E93' } }} />
                )}
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>

      {/* Right Chart - Weather Distribution */}
      <div className="flex-1 bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">天气状况分布</h3>
        </div>
        <div className="flex flex-col items-center gap-4">
          {pieData.length === 0 ? (
            <div className="h-[200px] flex items-center justify-center text-sm text-[#8E8E93]">暂无数据</div>
          ) : (
            <>
              <div className="relative w-[200px] h-[200px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={60} outerRadius={90}
                      paddingAngle={2} dataKey="value">
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
