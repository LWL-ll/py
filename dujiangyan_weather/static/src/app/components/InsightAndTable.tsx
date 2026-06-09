import { useState, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

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

export default function InsightAndTable() {
  const { selectedMonth, refreshKey } = useMonth();
  const [advice, setAdvice] = useState<AdviceData | null>(null);
  const [activeTab, setActiveTab] = useState('clothing');
  const [loading, setLoading] = useState(true);
  const [postcardText, setPostcardText] = useState('');
  const [postcardLoading, setPostcardLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    setPostcardLoading(true);

    Promise.all([
      fetch(`/api/weather/advice/?month=${selectedMonth}`).then((r) => r.json()),
      fetch('/api/weather/ai-postcard/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1] || '',
        },
        body: JSON.stringify({ month: selectedMonth }),
      }).then((r) => r.json()),
    ])
      .then(([adviceJson, postcardJson]) => {
        if (adviceJson.code === 0) setAdvice(adviceJson.data);
        if (postcardJson.code === 0 && postcardJson.data?.text) {
          setPostcardText(postcardJson.data.text);
        }
      })
      .catch(console.error)
      .finally(() => {
        setLoading(false);
        setPostcardLoading(false);
      });
  }, [selectedMonth, refreshKey]);

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
            <div className="flex gap-1 mb-4 flex-wrap">
              {catKeys.map((key) => {
                const meta = CATEGORY_META[key] || { label: key, color: '#8E8E93' };
                const isActive = key === activeTab;
                return (
                  <button key={key} onClick={() => setActiveTab(key)}
                    className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors"
                    style={{
                      backgroundColor: isActive ? meta.color + '20' : 'transparent',
                      color: isActive ? meta.color : '#8E8E93',
                      border: isActive ? `1px solid ${meta.color}40` : '1px solid transparent',
                    }}>
                    {meta.label}
                  </button>
                );
              })}
            </div>

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

      {/* Right Card - AI Weather Postcard */}
      <div className="flex-[2] bg-white border border-[#E8E8E6] rounded-[20px] shadow-[0_2px_12px_rgba(0,0,0,0.04)] max-h-[420px] flex flex-col">
        <div className="px-6 py-4 shrink-0">
          <h3 className="text-lg font-semibold text-[#1C1C1E]">天气明信片</h3>
        </div>
        <div className="flex-1 flex items-center justify-center p-6">
          {postcardLoading ? (
            <div className="flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
              <span className="text-sm text-[#8E8E93]">AI 生成明信片...</span>
            </div>
          ) : postcardText ? (
            <div className="relative w-full rounded-2xl overflow-hidden shadow-lg"
              style={{ aspectRatio: '4/3', maxWidth: 480 }}>
              {/* 真实风景照片背景 */}
              <img
                src={`https://source.unsplash.com/800x600/?chinese,mountain,landscape&sig=${encodeURIComponent(selectedMonth)}`}
                alt=""
                className="absolute inset-0 w-full h-full object-cover"
                loading="lazy"
              />
              {/* 暗色遮罩 */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-black/20 to-black/10"></div>

              {/* 文字覆盖层 */}
              <div className="absolute inset-0 flex flex-col items-center justify-center p-6 text-center">
                <p className="text-[10px] text-white/50 mb-4 tracking-[0.25em] uppercase">Postcard from Dujiangyan</p>
                <p className="text-lg text-white leading-relaxed drop-shadow-[0_2px_8px_rgba(0,0,0,0.5)] italic max-w-xs">
                  "{postcardText}"
                </p>
                <div className="absolute bottom-4 left-0 right-0 text-center">
                  <p className="text-[11px] text-white/40">都江堰 · {selectedMonth}</p>
                </div>
              </div>
            </div>
          ) : (
            <span className="text-sm text-[#8E8E93]">生成失败，请稍后再试</span>
          )}
        </div>
      </div>
    </div>
  );
}
