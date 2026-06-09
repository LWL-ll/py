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

interface AdviceCategory {
  advice: string;
  tags: string[];
  level?: string;
}

interface AdviceData {
  month: string;
  advice_text: string;
  tags: string[];
  categories: Record<string, AdviceCategory>;
}

const CATEGORY_META: Record<string, { label: string; color: string }> = {
  clothing: { label: '穿衣', color: '#D4A373' },
  travel:   { label: '出行', color: '#7FA3C1' },
  exercise: { label: '运动', color: '#81B29A' },
  health:   { label: '健康', color: '#4A6FA5' },
  alert:    { label: '预警', color: '#E07A5F' },
};

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
    <span className="inline-block px-3 py-1 rounded-full text-xs font-medium"
      style={{ backgroundColor: style.bg, border: `1px solid ${style.border}`, color: style.text }}>
      {weather || '-'}
    </span>
  );
};

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
  const [activeTab, setActiveTab] = useState('clothing');
  const [rows, setRows] = useState<WeatherRow[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const pageSize = 30;

  useEffect(() => {
    setLoading(true);
    setPage(1);
    const year = selectedMonth.split('-')[0];
    const month = selectedMonth.split('-')[1];

    Promise.all([
      fetch(`/api/weather/advice/?month=${selectedMonth}`).then((r) => r.json()),
      fetch(`/api/weather/list/?year=${year}&month=${month}&page=1&page_size=${pageSize}`).then((r) => r.json()),
    ])
      .then(([adviceJson, listJson]) => {
        if (adviceJson.code === 0) setAdvice(adviceJson.data);
        if (listJson.code === 0) {
          setRows(listJson.data || []);
          setTotal(listJson.total || 0);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [selectedMonth, refreshKey]);

  const loadPage = (p: number) => {
    setLoading(true);
    setPage(p);
    const year = selectedMonth.split('-')[0];
    const month = selectedMonth.split('-')[1];
    fetch(`/api/weather/list/?year=${year}&month=${month}&page=${p}&page_size=${pageSize}`)
      .then((res) => res.json())
      .then((json) => { if (json.code === 0) setRows(json.data || []); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const cats = advice?.categories || {};
  const catKeys = Object.keys(cats);
  const activeCat = cats[activeTab] || null;

  return (
    <div className="w-full flex flex-col lg:flex-row gap-6">
      {/* Left Card - Multi-tab Advice */}
      <div className="flex-1 lg:max-w-[33%] bg-gradient-to-br from-[#F5F5F0] to-[#FAFAF8] border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
        <h3 className="text-lg font-semibold text-[#1C1C1E] mb-3">智能生活建议</h3>

        {loading && !advice ? (
          <div className="flex items-center gap-2 py-8">
            <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
            <span className="text-sm text-[#8E8E93]">加载建议...</span>
          </div>
        ) : catKeys.length === 0 ? (
          <div className="py-8 text-center text-sm text-[#8E8E93]">暂无建议数据，请先执行数据分析</div>
        ) : (
          <>
            {/* Tab bar */}
            <div className="flex gap-1 mb-4 flex-wrap">
              {catKeys.map((key) => {
                const meta = CATEGORY_META[key] || { label: key, color: '#8E8E93' };
                const isActive = key === activeTab;
                return (
                  <button
                    key={key}
                    onClick={() => setActiveTab(key)}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                    style={{
                      backgroundColor: isActive ? meta.color + '20' : 'transparent',
                      color: isActive ? meta.color : '#8E8E93',
                      border: isActive ? `1px solid ${meta.color}40` : '1px solid transparent',
                    }}
                  >
                    {meta.label}
                  </button>
                );
              })}
            </div>

            {/* Active advice content */}
            {activeCat && (
              <div>
                {activeCat.level && activeCat.level !== 'normal' && (
                  <div className={`mb-3 px-3 py-1.5 rounded-lg text-xs font-bold ${
                    activeCat.level === 'danger' ? 'bg-[#E07A5F20] text-[#E07A5F]' : 'bg-[#D4A37320] text-[#D4A373]'
                  }`}>
                    {activeCat.level === 'danger' ? '需关注' : '请注意'}
                  </div>
                )}
                <p className="text-[14px] text-[#4A4A4A] leading-relaxed mb-4">{activeCat.advice}</p>
                <div className="flex flex-wrap gap-2">
                  {(activeCat.tags || []).map((tag: string) => (
                    <span key={tag} className="px-3 py-1 rounded-full text-xs font-medium"
                      style={{
                        backgroundColor: (CATEGORY_META[activeTab]?.color || '#8E8E93') + '20',
                        color: CATEGORY_META[activeTab]?.color || '#8E8E93',
                      }}>
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>

      {/* Right Card - Weather Table / Postcard */}
      <PostcardOrTable loading={loading} rows={rows} total={total} page={page} pageSize={pageSize}
        totalPages={totalPages} loadPage={loadPage} selectedMonth={selectedMonth} refreshKey={refreshKey} />
    </div>
  );
}

// ───── 右侧卡片：明信片 / 表格切换 ─────

function PostcardOrTable({ loading, rows, total, page, pageSize, totalPages, loadPage, selectedMonth, refreshKey }: {
  loading: boolean; rows: WeatherRow[]; total: number; page: number; pageSize: number;
  totalPages: number; loadPage: (p: number) => void; selectedMonth: string; refreshKey: number;
}) {
  const [view, setView] = useState<'table' | 'postcard'>('table');
  const [postcardText, setPostcardText] = useState('');
  const [postcardLoading, setPostcardLoading] = useState(false);

  useEffect(() => {
    if (view === 'postcard' && !postcardText) {
      setPostcardLoading(true);
      fetch('/api/weather/ai-postcard/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ month: selectedMonth }),
      })
        .then((r) => r.json())
        .then((json) => {
          if (json.code === 0) setPostcardText(json.data?.text || '');
        })
        .catch(() => {})
        .finally(() => setPostcardLoading(false));
    }
  }, [view, selectedMonth, refreshKey]);

  return (
    <div className="flex-[2] bg-white border border-[#E8E8E6] rounded-[20px] overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.04)] max-h-[420px] flex flex-col">
      <div className="px-6 py-4 shrink-0 flex items-center justify-between">
        <h3 className="text-lg font-semibold text-[#1C1C1E]">
          {view === 'table' ? '当月天气明细' : '天气明信片'}
        </h3>
        <div className="flex bg-[#FAFAF8] rounded-lg p-0.5">
          {(['table', 'postcard'] as const).map((v) => (
            <button key={v} onClick={() => setView(v)}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                view === v ? 'bg-white text-[#4A6FA5] shadow-sm' : 'text-[#8E8E93] hover:text-[#4A6FA5]'
              }`}>
              {v === 'table' ? '表格' : '明信片'}
            </button>
          ))}
        </div>
      </div>

      {view === 'postcard' ? (
        <div className="flex-1 flex items-center justify-center p-6">
          {postcardLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
              <span className="text-sm text-[#8E8E93]">AI 生成明信片...</span>
            </div>
          ) : postcardText ? (
            <div className="bg-gradient-to-br from-[#4A6FA508] via-[#7FA3C108] to-[#81B29A08] border border-[#4A6FA520] rounded-2xl p-8 max-w-sm text-center">
              <p className="text-xs text-[#8E8E93] mb-3 tracking-widest">POSTCARD FROM DUJIANGYAN</p>
              <p className="text-lg text-[#4A4A4A] leading-relaxed italic">"{postcardText}"</p>
              <div className="mt-4 pt-4 border-t border-[#4A6FA515]">
                <p className="text-[11px] text-[#B0B0B0]">都江堰 · {selectedMonth}</p>
              </div>
            </div>
          ) : (
            <span className="text-sm text-[#8E8E93]">生成失败，请稍后再试</span>
          )}
        </div>
      ) : (
        <>
        <div className="overflow-auto flex-1">
          <table className="w-full">
            <thead className="sticky top-0 z-10">
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
                <tr><td colSpan={5} className="py-12 text-center">
                  <Loader2 className="w-5 h-5 animate-spin text-[#8E8E93] inline-block" />
                  <span className="ml-2 text-sm text-[#8E8E93]">加载数据...</span>
                </td></tr>
              ) : rows.length === 0 ? (
                <tr><td colSpan={5} className="py-12 text-center text-sm text-[#8E8E93]">
                  暂无数据，请先点击"一键爬取"
                </td></tr>
              ) : (
                rows.map((row, index) => (
                  <tr key={row.date} className={`h-[52px] hover:bg-[#FAFAF8] transition-colors ${index % 2 === 0 ? 'bg-white' : 'bg-[#FAFAF8]'}`}>
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

        {total > pageSize && (
          <div className="h-12 flex items-center justify-center gap-2 border-t border-[#E8E8E6] shrink-0">
            <button onClick={() => page > 1 && loadPage(page - 1)} disabled={page <= 1}
              className="w-6 h-6 rounded-full flex items-center justify-center text-[13px] text-[#8E8E93] hover:bg-[#FAFAF8] disabled:opacity-30">‹</button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const start = Math.max(1, Math.min(page - 2, totalPages - 4));
              const p = start + i;
              if (p > totalPages) return null;
              return (
                <button key={p} onClick={() => loadPage(p)}
                  className={`w-6 h-6 rounded-full flex items-center justify-center text-[13px] ${p === page ? 'bg-[#4A6FA5] text-white' : 'text-[#8E8E93] hover:bg-[#FAFAF8]'}`}>
                  {p}
                </button>
              );
            })}
            <button onClick={() => page < totalPages && loadPage(page + 1)} disabled={page >= totalPages}
              className="w-6 h-6 rounded-full flex items-center justify-center text-[13px] text-[#8E8E93] hover:bg-[#FAFAF8] disabled:opacity-30">›</button>
          </div>
        )}
        </>
      )}
      </div>
  );
}
