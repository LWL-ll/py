import { useState, useEffect } from 'react';
import { Sun, CloudRain, ThermometerSun, ThermometerSnowflake, Loader2 } from 'lucide-react';
import StatsCard from './StatsCard';
import { useMonth } from '../context/MonthContext';

interface SummaryData {
  sunny_probability: number;
  rainy_probability: number;
  avg_max_temp: number | null;
  avg_min_temp: number | null;
  date_range: string;
  total_days: number;
  monthly_avg_max_temp: number | null;
  monthly_avg_min_temp: number | null;
}

export default function StatsGrid() {
  const { selectedMonth, refreshKey } = useMonth();
  const [data, setData] = useState<SummaryData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch('/api/weather/summary/')
      .then((res) => res.json())
      .then((json) => {
        if (json.code === 0) {
          setData(json.data);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedMonth, refreshKey]);

  if (loading && !data) {
    return (
      <div className="w-full flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 animate-spin text-[#8E8E93]" />
        <span className="ml-2 text-sm text-[#8E8E93]">加载统计数据...</span>
      </div>
    );
  }

  return (
    <div className="w-full flex flex-wrap gap-4">
      <StatsCard
        icon={Sun}
        label="晴天概率"
        value={data ? `${data.sunny_probability}%` : '-'}
        accentColor="#D4A373"
        sparklineColor="#D4A373"
      />
      <StatsCard
        icon={CloudRain}
        label="雨天概率"
        value={data ? `${data.rainy_probability}%` : '-'}
        accentColor="#7FA3C1"
        sparklineColor="#7FA3C1"
      />
      <StatsCard
        icon={ThermometerSun}
        label="月均最高温"
        value={data?.monthly_avg_max_temp != null ? `${data.monthly_avg_max_temp}°C` : '-'}
        accentColor="#E07A5F"
        sparklineColor="#E07A5F"
      />
      <StatsCard
        icon={ThermometerSnowflake}
        label="月均最低温"
        value={data?.monthly_avg_min_temp != null ? `${data.monthly_avg_min_temp}°C` : '-'}
        accentColor="#81B29A"
        sparklineColor="#81B29A"
      />
    </div>
  );
}
