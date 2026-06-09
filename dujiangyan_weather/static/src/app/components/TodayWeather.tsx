import { useState, useEffect } from 'react';
import { Loader2, Droplets, Wind, CloudRain } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface TodayData {
  date: string;
  max_temp: number | null;
  min_temp: number | null;
  weather_desc: string;
  humidity: number | null;
  wind_direction: string;
  wind_level: string;
  rainy_days?: number;
}

export default function TodayWeather() {
  const { refreshKey } = useMonth();
  const [data, setData] = useState<TodayData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch('/api/weather/today/')
      .then((r) => r.json())
      .then((json) => {
        if (json.code === 0) setData(json.data);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [refreshKey]);

  if (loading) {
    return (
      <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-5 flex items-center justify-center gap-2 shadow-sm">
        <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
        <span className="text-sm text-[#8E8E93]">加载今日天气...</span>
      </div>
    );
  }

  if (!data || !data.weather_desc) return null;

  const windText = [data.wind_direction, data.wind_level].filter(Boolean).join(' ') || '-';

  return (
    <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
        <h3 className="text-sm font-semibold text-[#1C1C1E]">今日天气</h3>
        <span className="text-[11px] text-[#8E8E93] ml-auto">{data.date}</span>
      </div>

      <div className="flex items-center gap-5 mb-5">
        <div>
          <p className="text-3xl font-bold text-[#1C1C1E]">
            {data.min_temp != null ? `${Math.round(data.min_temp)}°` : '?'} ~ {data.max_temp != null ? `${Math.round(data.max_temp)}°` : '?'}
          </p>
          <p className="text-sm text-[#6E6E73] mt-0.5">{data.weather_desc}</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3">
        <div className="bg-[#FAFAF8] rounded-xl p-3 flex items-center gap-2">
          <Droplets className="w-5 h-5 text-[#7FA3C1] shrink-0" />
          <div className="min-w-0">
            <p className="text-[10px] text-[#8E8E93]">湿度</p>
            <p className="text-sm font-semibold text-[#1C1C1E] truncate">
              {data.humidity != null ? `${data.humidity}%` : '-'}
            </p>
          </div>
        </div>

        <div className="bg-[#FAFAF8] rounded-xl p-3 flex items-center gap-2">
          <Wind className="w-5 h-5 text-[#A8A29E] shrink-0" />
          <div className="min-w-0">
            <p className="text-[10px] text-[#8E8E93]">风力风向</p>
            <p className="text-sm font-semibold text-[#1C1C1E] truncate">{windText}</p>
          </div>
        </div>

        <div className="bg-[#FAFAF8] rounded-xl p-3 flex items-center gap-2">
          <CloudRain className="w-5 h-5 text-[#4A6FA5] shrink-0" />
          <div className="min-w-0">
            <p className="text-[10px] text-[#8E8E93]">本月降雨</p>
            <p className="text-sm font-semibold text-[#1C1C1E]">
              {data.rainy_days != null ? `${data.rainy_days} 天` : '-'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
