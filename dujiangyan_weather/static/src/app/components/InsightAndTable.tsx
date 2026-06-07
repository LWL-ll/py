import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface WeatherRow {
  date: string;
  max_temp: number | null;
  min_temp: number | null;
  weather_desc: string;
  wind_direction: string;
  wind_level: string;
  weather_type?: string;
}

interface AdviceData {
  month: string;
  advice_text: string;
  tags: string[];
}

const WeatherPill = ({ weather, type }: { weather: string; type: string }) => {
  const styles: Record<string, { bg: string; border: string; text: string }> = {
    sunny: { bg: '#D4A37326', border: '#D4A3734D', text: '#D4A373' },
    rainy: { bg: '#7FA3C126', border: '#7FA3C14D', text: '#7FA3C1' },
    overcast: { bg: '#A8A29E26', border: '#A8A29E4D', text: '#78716C' },
    cloudy: { bg: '#A8A29E26', border: '#A8A29E4D', text: '#A8A29E' },
    snowy: { bg: '#B8C5D626', border: '#B8C5D64D', text: '#B8C5D6' },
    foggy: { bg: '#9CA3AF26', border: '#9CA3AF4D', text: '#9CA3AF' },
  };
  const style = styles[type] || styles.overcast;

  return (
    <span
      className="inline-block px-3 py-1 rounded-full text-xs font-medium"
      style={{
        backgroundColor: style.bg,
        border: `1px solid ${style.border}`,
        color: style.text,
      }}
    >
      {weather || '-'}
    </span>
  );
};

/** 根据天气描述推断 weather_type（前端辅助） */
function inferType(desc: string): string {
  if (!desc) return '';
  if (desc.includes('雪')) return 'snowy';
  if (desc.includes('雨')) return 'rainy';
  if (desc.includes('雾') || desc.includes('霾')) return 'foggy';
  if (desc.includes('多云')) return 'cloudy';
  if (desc.includes('阴')) return 'overcast';
  if (desc.includes('晴')) return 'sunny';
  return '';
}

export default function InsightAndTable() {
  const { selectedMonth, refreshKey } = useMonth();
  const [advice, setAdvice] = useState<AdviceData | null>(null);
  const [rows, setRows] = useState<WeatherRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const pageSize = 30;

  useEffect(() => {
    setLoading(true);
    setPage(1); // 切换月份回到第一页
    const year = selectedMonth.split('-')[0];
    const month = selectedMonth.split('-')[1];

    Promise.all([
      fetch(`/api/weather/advice/?month=${selectedMonth}`).then((r) => r.json()),
      fetch(`/api/weather/list/?year=${year}&month=${month}&page=1&page_size=${pageSize}`).then((r) => r.json()),
    ])
      .then(([adviceJson, listJson]) => {
        if (adviceJson.code === 0) {
          setAdvice(adviceJson.data);
        }
        if (listJson.code === 0) {
          setRows(listJson.data || []);
          setTotal(listJson.total || 0);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedMonth, refreshKey]);

  /** 翻页 */
  const loadPage = (p: number) => {
    setLoading(true);
    setPage(p);
    const year = selectedMonth.split('-')[0];
    const month = selectedMonth.split('-')[1];
    fetch(`/api/weather/list/?year=${year}&month=${month}&page=${p}&page_size=${pageSize}`)
      .then((res) => res.json())
      .then((json) => {
        if (json.code === 0) {
          setRows(json.data || []);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div className="w-full flex flex-col lg:flex-row gap-6">
      {/* Left Card - Clothing Advice (1/3 width) */}
      <div className="flex-1 lg:max-w-[33%] bg-gradient-to-br from-[#F5F5F0] to-[#FAFAF8] border border-[#E8E8E6] rounded-[20px] p-7 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
        <h3 className="text-lg font-semibold text-[#1C1C1E] mb-4">🧥 智能穿衣建议</h3>

        {loading && !advice ? (
          <div className="flex items-center gap-2 py-8">
            <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
            <span className="text-sm text-[#8E8E93]">加载建议...</span>
          </div>
        ) : advice ? (
          <>
            <div className="text-[40px] text-[#D4A373] mb-4 leading-none">"</div>
            <p className="text-[15px] text-[#4A4A4A] leading-relaxed mb-4">{advice.advice_text}</p>
            <div className="flex flex-wrap gap-2">
              {(advice.tags || []).map((tag) => (
                <span
                  key={tag}
                  className="px-3 py-1.5 rounded-full text-xs font-medium"
                  style={{ backgroundColor: '#D4A37326', color: '#D4A373' }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </>
        ) : (
          <div className="py-8 text-center text-sm text-[#8E8E93]">
            暂无穿衣建议，请先执行数据分析
          </div>
        )}
      </div>

      {/* Right Card - Weather Table (2/3 width) */}
      <div className="flex-[2] bg-white border border-[#E8E8E6] rounded-[20px] overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
        <div className="px-6 py-4">
          <h3 className="text-lg font-semibold text-[#1C1C1E]">📋 当月天气明细</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-[#F5F5F0] h-12">
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">日期</th>
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">最高温(°C)</th>
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">最低温(°C)</th>
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">天气状况</th>
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">风力</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center">
                    <Loader2 className="w-5 h-5 animate-spin text-[#8E8E93] inline-block" />
                    <span className="ml-2 text-sm text-[#8E8E93]">加载数据...</span>
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-sm text-[#8E8E93]">
                    暂无数据，请先点击"一键爬取"
                  </td>
                </tr>
              ) : (
                rows.map((row, index) => (
                  <tr
                    key={row.date}
                    className={`h-[52px] hover:bg-[#FAFAF8] transition-colors ${
                      index % 2 === 0 ? 'bg-white' : 'bg-[#FAFAF8]'
                    }`}
                  >
                    <td className="px-4 text-center text-sm text-[#4A4A4A]">{row.date}</td>
                    <td className="px-4 text-center text-sm text-[#4A4A4A]">{row.max_temp ?? '-'}</td>
                    <td className="px-4 text-center text-sm text-[#4A4A4A]">{row.min_temp ?? '-'}</td>
                    <td className="px-4 text-center">
                      <WeatherPill weather={row.weather_desc} type={row.weather_type || inferType(row.weather_desc)} />
                    </td>
                    <td className="px-4 text-center text-sm text-[#4A4A4A]">
                      {row.wind_direction || ''} {row.wind_level || ''}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        {total > pageSize && (
          <div className="h-12 flex items-center justify-center gap-2 border-t border-[#E8E8E6]">
            <button
              onClick={() => page > 1 && loadPage(page - 1)}
              disabled={page <= 1}
              className="w-6 h-6 rounded-full flex items-center justify-center text-[13px] text-[#8E8E93] hover:bg-[#FAFAF8] disabled:opacity-30"
            >
              ‹
            </button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              // 显示当前页附近的页码
              const start = Math.max(1, Math.min(page - 2, totalPages - 4));
              const p = start + i;
              if (p > totalPages) return null;
              return (
                <button
                  key={p}
                  onClick={() => loadPage(p)}
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[13px] ${
                    p === page ? 'bg-[#4A6FA5] text-white' : 'text-[#8E8E93] hover:bg-[#FAFAF8]'
                  }`}
                >
                  {p}
                </button>
              );
            })}
            <button
              onClick={() => page < totalPages && loadPage(page + 1)}
              disabled={page >= totalPages}
              className="w-6 h-6 rounded-full flex items-center justify-center text-[13px] text-[#8E8E93] hover:bg-[#FAFAF8] disabled:opacity-30"
            >
              ›
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
