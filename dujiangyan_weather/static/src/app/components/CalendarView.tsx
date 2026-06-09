import { useState, useEffect } from 'react';
import { Loader2, ChevronLeft, ChevronRight, CloudRain, CloudSnow, Cloud, CloudFog, Sun } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface DayInfo {
  date: string;
  day: number;
  is_current_month: boolean;
  is_today: boolean;
  max_temp?: number | null;
  min_temp?: number | null;
  weather_desc?: string;
  weather_type?: string;
  source?: string;
}

function MiniWeatherIcon({ type, desc }: { type?: string; desc?: string }) {
  const cls = 'w-5 h-5';
  const d = desc || '';
  if (d.includes('雪') || type === 'snowy') return <CloudSnow className={`${cls} text-[#B8C5D6]`} />;
  if (d.includes('雨') || type === 'rainy') return <CloudRain className={`${cls} text-[#7FA3C1]`} />;
  if (d.includes('雾') || d.includes('霾') || type === 'foggy') return <CloudFog className={`${cls} text-[#9CA3AF]`} />;
  if (d.includes('多云') || type === 'cloudy') return <Cloud className={`${cls} text-[#A8A29E]`} />;
  if (d.includes('阴') || type === 'overcast') return <Cloud className={`${cls} text-[#78716C]`} />;
  if (d.includes('晴') || type === 'sunny') return <Sun className={`${cls} text-[#D4A373]`} />;
  return <Sun className={`${cls} text-[#D4A373]`} />;
}

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日'];
const MONTHS = ['1月','2月','3月','4月','5月','6月','7月','8月','9月','10月','11月','12月'];

export default function CalendarView() {
  const { selectedMonth, setSelectedMonth } = useMonth();
  const [weeks, setWeeks] = useState<DayInfo[][]>([]);
  const [loading, setLoading] = useState(true);
  const [displayYear, setDisplayYear] = useState(2026);
  const [displayMonth, setDisplayMonth] = useState(6);
  const [tooltip, setTooltip] = useState<{ day: DayInfo; x: number; y: number } | null>(null);

  useEffect(() => {
    const [y, m] = selectedMonth.split('-').map(Number);
    setDisplayYear(y);
    setDisplayMonth(m);
    fetchCalendar(y, m);
  }, [selectedMonth]);

  const fetchCalendar = (year: number, month: number) => {
    setLoading(true);
    fetch(`/api/weather/calendar/?year=${year}&month=${month}`)
      .then((r) => r.json())
      .then((json) => {
        if (json.code === 0) setWeeks(json.data?.weeks || []);
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const goMonth = (delta: number) => {
    let m = displayMonth + delta;
    let y = displayYear;
    if (m < 1) { m = 12; y--; }
    if (m > 12) { m = 1; y++; }
    setDisplayYear(y);
    setDisplayMonth(m);
    setSelectedMonth(`${y}-${String(m).padStart(2, '0')}`);
    fetchCalendar(y, m);
  };

  return (
    <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-5 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-[#1C1C1E]">天气月历</h3>
        <div className="flex items-center gap-2">
          <button onClick={() => goMonth(-1)} className="p-1 rounded-lg hover:bg-[#FAFAF8]">
            <ChevronLeft className="w-4 h-4 text-[#8E8E93]" />
          </button>
          <span className="text-sm font-medium text-[#1C1C1E]">
            {displayYear}年{MONTHS[displayMonth - 1]}
          </span>
          <button onClick={() => goMonth(1)} className="p-1 rounded-lg hover:bg-[#FAFAF8]">
            <ChevronRight className="w-4 h-4 text-[#8E8E93]" />
          </button>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-5 h-5 animate-spin text-[#8E8E93]" />
        </div>
      ) : (
        <div className="flex flex-col gap-1">
          {/* Weekday headers */}
          <div className="grid grid-cols-7 mb-1">
            {WEEKDAYS.map((d) => (
              <div key={d} className="text-center text-[11px] font-medium text-[#8E8E93] py-1">{d}</div>
            ))}
          </div>

          {/* Days grid */}
          {weeks.map((week, wi) => (
            <div key={wi} className="grid grid-cols-7 gap-0.5">
              {week.map((day, di) => {
                const isHist = day.source === 'history';
                const isFc = day.source === 'forecast';
                return (
                <div
                  key={di}
                  className={`aspect-square rounded-lg flex flex-col items-center justify-center p-1.5 transition-colors relative cursor-default ${
                    !day.is_current_month
                      ? 'opacity-20'
                      : day.is_today
                      ? 'bg-[#4A6FA5] text-white font-medium'
                      : isHist
                      ? 'bg-[#4A6FA508] border border-[#4A6FA525] hover:bg-[#4A6FA515]'
                      : isFc
                      ? 'border-2 border-dashed border-[#8E8E9330] hover:bg-[#FAFAF8]'
                      : 'hover:bg-[#FAFAF8]'
                  }`}
                  onMouseEnter={(e) => {
                    if (day.is_current_month && day.weather_desc) {
                      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect();
                      setTooltip({ day, x: rect.left + rect.width / 2, y: rect.top - 10 });
                    }
                  }}
                  onMouseLeave={() => setTooltip(null)}
                >
                  <span className={`text-xs ${day.is_today ? 'font-bold' : ''}`}>{day.day}</span>
                  {day.is_current_month && day.weather_desc && (
                    <>
                      <MiniWeatherIcon type={day.weather_type} desc={day.weather_desc} />
                      <span className={`text-[11px] leading-tight font-medium ${day.is_today ? 'text-white/80' : isFc ? 'text-[#B0B0B0]' : 'text-[#4A4A4A]'}`}>
                        {day.max_temp != null ? `${Math.round(day.max_temp)}°` : ''}
                      </span>
                    </>
                  )}
                </div>
              )})}
            </div>
          ))}
        </div>
      )}

      {/* Legend */}
      <div className="flex items-center justify-center gap-4 mt-3 pt-3 border-t border-[#E8E8E6]">
        <span className="flex items-center gap-1.5 text-[10px] text-[#6E6E73]">
          <span className="w-3 h-3 rounded bg-[#4A6FA510] border border-[#4A6FA530] inline-block"></span>
          历史数据
        </span>
        <span className="flex items-center gap-1.5 text-[10px] text-[#8E8E93]">
          <span className="w-3 h-3 rounded border-2 border-dashed border-[#8E8E9340] inline-block"></span>
          预报数据
        </span>
      </div>

      {/* 悬浮提示——固定定位在视口上方 */}
      {tooltip && (
        <div
          className="fixed left-0 top-0 z-[9999] pointer-events-none"
          style={{
            transform: `translate(${tooltip.x}px, ${tooltip.y}px) translate(-50%, -100%)`,
          }}
        >
          <div className="bg-white border border-[#E8E8E6] rounded-xl px-3 py-2 shadow-xl animate-fadeIn">
            <p className="text-xs font-medium text-[#1C1C1E] mb-1">{tooltip.day.date}</p>
            <div className="flex items-center gap-2">
              <MiniWeatherIcon type={tooltip.day.weather_type} desc={tooltip.day.weather_desc} />
              <span className="text-xs text-[#4A4A4A]">{tooltip.day.weather_desc}</span>
            </div>
            <p className="text-xs text-[#8E8E93] mt-1">
              {tooltip.day.min_temp != null ? `${tooltip.day.min_temp}°C` : '?'} ~ {tooltip.day.max_temp != null ? `${tooltip.day.max_temp}°C` : '?'}
            </p>
            <p className="text-[10px] text-[#B0B0B0]">
              {tooltip.day.source === 'history' ? '历史数据' : tooltip.day.source === 'forecast' ? '预报数据' : ''}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
