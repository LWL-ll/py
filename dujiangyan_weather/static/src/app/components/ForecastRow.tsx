import { useState, useEffect } from 'react';
import { Loader2, CloudSun, CloudRain, CloudSnow, Cloud, CloudFog, Sun } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface ForecastItem {
  date: string;
  day_temp: number | null;
  night_temp: number | null;
  weather_desc: string;
  week: string;
}

/** 天气→图标映射 */
function WeatherIcon({ desc }: { desc: string }) {
  const cls = 'w-7 h-7';
  if (!desc) return <CloudSun className={cls} />;
  if (desc.includes('雨')) return <CloudRain className={`${cls} text-[#7FA3C1]`} />;
  if (desc.includes('雪')) return <CloudSnow className={`${cls} text-[#B8C5D6]`} />;
  if (desc.includes('多云')) return <Cloud className={`${cls} text-[#A8A29E]`} />;
  if (desc.includes('阴')) return <Cloud className={`${cls} text-[#78716C]`} />;
  if (desc.includes('晴')) return <Sun className={`${cls} text-[#D4A373]`} />;
  if (desc.includes('雾') || desc.includes('霾')) return <CloudFog className={`${cls} text-[#9CA3AF]`} />;
  return <CloudSun className={cls} />;
}

export default function ForecastRow() {
  const { refreshKey } = useMonth();
  const [forecast, setForecast] = useState<ForecastItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch('/api/weather/forecast/')
      .then((res) => res.json())
      .then((json) => {
        if (json.code === 0 && json.data?.length) {
          setForecast(json.data.slice(0, 8));
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [refreshKey]);

  if (loading) {
    return (
      <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-4 flex items-center justify-center gap-2 shadow-sm">
        <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
        <span className="text-sm text-[#8E8E93]">加载预报...</span>
      </div>
    );
  }

  if (forecast.length === 0) return null;

  return (
    <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-5 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
      <h3 className="text-sm font-semibold text-[#1C1C1E] mb-3">未来天气预报</h3>
      <div className="flex gap-3 overflow-x-auto pb-1">
        {forecast.map((item) => (
          <div
            key={item.date}
            className="flex-shrink-0 w-[100px] bg-[#FAFAF8] rounded-xl p-3 flex flex-col items-center gap-1 hover:shadow-md transition-shadow"
          >
            <span className="text-[11px] text-[#8E8E93]">{item.week || item.date.slice(5)}</span>
            <WeatherIcon desc={item.weather_desc} />
            <span className="text-[11px] text-[#6E6E73] truncate w-full text-center">
              {item.weather_desc}
            </span>
            <div className="flex gap-2 text-xs font-medium">
              <span className="text-[#E07A5F]">{item.day_temp ?? '-'}°</span>
              <span className="text-[#7FA3C1]">{item.night_temp ?? '-'}°</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
