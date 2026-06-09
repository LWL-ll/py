import { useState, useEffect } from 'react';
import { Loader2, RefreshCw, Sparkles } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

export default function WeatherDiary() {
  const { selectedMonth, refreshKey } = useMonth();
  const [diary, setDiary] = useState('');
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    generateDiary();
  }, [selectedMonth, refreshKey]);

  const generateDiary = async () => {
    setGenerating(true);
    try {
      const res = await fetch('/api/weather/ai-diary/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
        body: JSON.stringify({ month: selectedMonth }),
      });
      const json = await res.json();
      if (json.code === 0 && json.data?.diary) {
        setDiary(json.data.diary);
      }
    } catch {
      setDiary('日记生成失败，请稍后再试。');
    } finally {
      setLoading(false);
      setGenerating(false);
    }
  };

  if (loading) {
    return (
      <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-5 flex items-center justify-center gap-2 shadow-sm">
        <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
        <span className="text-sm text-[#8E8E93]">生成天气日记...</span>
      </div>
    );
  }

  if (!diary) return null;

  return (
    <div className="w-full bg-gradient-to-br from-[#FAFAF8] to-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04)]">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-[#4A6FA5]" />
          <h3 className="text-sm font-semibold text-[#1C1C1E]">AI 天气日记</h3>
        </div>
        <button
          onClick={generateDiary}
          disabled={generating}
          className="p-1.5 rounded-lg hover:bg-[#FAFAF8] transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 text-[#8E8E93] ${generating ? 'animate-spin' : ''}`} />
        </button>
      </div>
      <p className="text-[14px] text-[#4A4A4A] leading-relaxed whitespace-pre-line">{diary}</p>
    </div>
  );
}

function getCsrf(): string {
  const m = document.cookie.match(/csrftoken=([^;]+)/);
  return m ? m[1] : '';
}
