import { useState, useEffect } from 'react';
import { Loader2, Thermometer, Droplets, Wind, Gauge, CloudRain, CloudSnow, Cloud, CloudFog, Sun } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface TodayData {
  date: string;
  max_temp: number | null;
  min_temp: number | null;
  weather_desc: string;
  humidity: number | null;
  wind_direction: string;
  wind_level: string;
  air_quality_score: number | null;
  temp_comfort_score: number | null;
  source: string;
}

function WeatherIcon({ desc }: { desc: string }) {
  const cls = 'w-10 h-10';
  if (desc.includes('雪')) return <CloudSnow className={`${cls} text-[#B8C5D6]`} />;
  if (desc.includes('雨')) return <CloudRain className={`${cls} text-[#7FA3C1]`} />;
  if (desc.includes('雾') || desc.includes('霾')) return <CloudFog className={`${cls} text-[#9CA3AF]`} />;
  if (desc.includes('多云')) return <Cloud className={`${cls} text-[#A8A29E]`} />;
  if (desc.includes('阴')) return <Cloud className={`${cls} text-[#78716C]`} />;
  if (desc.includes('晴')) return <Sun className={`${cls} text-[#D4A373]`} />;
  return <Sun className={`${cls} text-[#D4A373]`} />;
}

function airQualityLabel(score: number | null): { text: string; color: string } {
  if (score == null) return { text: '暂无', color: '#8E8E93' };
  if (score >= 80) return { text: '优', color: '#81B29A' };
  if (score >= 60) return { text: '良', color: '#7FA3C1' };
  if (score >= 40) return { text: '一般', color: '#D4A373' };
  return { text: '较差', color: '#E07A5F' };
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

  const aq = airQualityLabel(data.air_quality_score);

  return (
    <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
        <h3 className="text-sm font-semibold text-[#1C1C1E]">今日天气</h3>
        <span className="text-[11px] text-[#8E8E93] ml-auto">{data.date}</span>
      </div>

      <div className="flex items-center gap-5 mb-5">
        <WeatherIcon desc={data.weather_desc} />
        <div>
          <p className="text-2xl font-bold text-[#1C1C1E]">
            {data.min_temp != null ? `${Math.round(data.min_temp)}°` : '?'} ~ {data.max_temp != null ? `${Math.round(data.max_temp)}°` : '?'}
          </p>
          <p className="text-sm text-[#6E6E73]">{data.weather_desc}</p>
        </div>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {/* 湿度 */}
        <div className="bg-[#FAFAF8] rounded-xl p-3 flex items-center gap-2">
          <Droplets className="w-5 h-5 text-[#7FA3C1]" />
          <div>
            <p className="text-[10px] text-[#8E8E93]">湿度</p>
            <p className="text-sm font-semibold text-[#1C1C1E]">{data.humidity != null ? `${data.humidity}%` : '-'}</p>
          </div>
        </div>

        {/* 风力 */}
        <div className="bg-[#FAFAF8] rounded-xl p-3 flex items-center gap-2">
          <Wind className="w-5 h-5 text-[#A8A29E]" />
          <div>
            <p className="text-[10px] text-[#8E8E93]">风力</p>
            <p className="text-sm font-semibold text-[#1C1C1E]">
              {data.wind_direction || data.wind_level ? `${data.wind_direction} ${data.wind_level}` : '-'}
            </p>
          </div>
        </div>

        {/* 体感/舒适度 */}
        <div className="bg-[#FAFAF8] rounded-xl p-3 flex items-center gap-2">
          <Thermometer className="w-5 h-5 text-[#E07A5F]" />
          <div>
            <p className="text-[10px] text-[#8E8E93]">舒适度</p>
            <p className="text-sm font-semibold text-[#1C1C1E]">
              {data.temp_comfort_score != null ? `${data.temp_comfort_score}分` : '-'}
            </p>
          </div>
        </div>

        {/* 空气质量 */}
        <div className="bg-[#FAFAF8] rounded-xl p-3 flex items-center gap-2">
          <Gauge className="w-5 h-5" style={{ color: aq.color }} />
          <div>
            <p className="text-[10px] text-[#8E8E93]">空气质量</p>
            <p className="text-sm font-semibold" style={{ color: aq.color }}>{aq.text}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
