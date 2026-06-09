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
            <div className="relative w-full max-w-sm rounded-2xl overflow-hidden shadow-lg" style={{ minHeight: 280 }}>
              {/* 油画风景背景 */}
              <div className="absolute inset-0" style={{
                background: `linear-gradient(180deg,
                  #7BA4CC 0%, #8DB5D6 15%, #C4D9E8 25%, #D4A37320 30%,
                  #81B29A40 35%, #5A8F6A60 45%, #4A7A5A80 55%,
                  #6A8A7060 65%, #7FA3C140 75%, #C4C8D030 100%)`,
              }}></div>
              {/* 油画笔触纹理 */}
              <div className="absolute inset-0 opacity-30" style={{
                backgroundImage: `radial-gradient(circle at 30% 40%, #D4A37310 0%, transparent 50%),
                  radial-gradient(circle at 70% 30%, #ffffff20 0%, transparent 40%),
                  radial-gradient(circle at 50% 70%, #4A6FA510 0%, transparent 60%),
                  radial-gradient(ellipse at 20% 80%, #3D5A8A15 0%, transparent 50%),
                  radial-gradient(circle at 80% 60%, #81B29A12 0%, transparent 40%)`,
              }}></div>
              {/* 远山轮廓 */}
              <div className="absolute bottom-0 left-0 right-0 h-[45%]" style={{
                background: `linear-gradient(180deg, transparent 0%, #5A8F6A30 10%, #4A7A5A50 30%, #3D5A3D70 60%, #2D4A2D90 100%)`,
                clipPath: 'polygon(0 60%, 15% 35%, 30% 50%, 45% 25%, 60% 45%, 75% 30%, 90% 48%, 100% 40%, 100% 100%, 0 100%)',
              }}></div>
              {/* 前景山丘 */}
              <div className="absolute bottom-0 left-0 right-0 h-[25%]" style={{
                background: `linear-gradient(180deg, #3D6A3D60 0%, #2D4A2D90 100%)`,
                clipPath: 'polygon(0 50%, 20% 30%, 40% 45%, 60% 20%, 80% 35%, 100% 25%, 100% 100%, 0 100%)',
              }}></div>
              {/* 江水反光 */}
              <div className="absolute bottom-[8%] left-[15%] right-[15%] h-[6%]" style={{
                background: 'linear-gradient(90deg, transparent, #7FA3C140, #C4D9E860, #7FA3C140, transparent)',
                borderRadius: '50%',
              }}></div>

              {/* 文字覆盖层 */}
              <div className="relative z-10 flex flex-col items-center justify-center h-full p-8 text-center">
                <p className="text-[10px] text-white/60 mb-3 tracking-[0.2em] uppercase">Postcard from Dujiangyan</p>
                <p className="text-base text-white leading-relaxed italic drop-shadow-lg">"{postcardText}"</p>
                <div className="mt-auto pt-4">
                  <p className="text-[11px] text-white/50">都江堰 · {selectedMonth}</p>
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
