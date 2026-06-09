import { useState } from 'react';
import { CloudDownload, Loader2, User } from 'lucide-react';
import { useMonth } from '../context/MonthContext';
import { useAuth } from '../context/AuthContext';
import { apiFetch } from '../utils/api';

export default function Navbar() {
  const { selectedMonth, setSelectedMonth, availableMonths, loading, triggerRefresh } = useMonth();
  const { user, logout } = useAuth();
  const [crawlLoading, setCrawlLoading] = useState(false);
  const [analyzeLoading, setAnalyzeLoading] = useState(false);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [statusMsg, setStatusMsg] = useState('系统就绪');

  /** 一键爬取 */
  const handleCrawl = async () => {
    setCrawlLoading(true);
    setStatusMsg('数据爬取中...');
    try {
      const res = await apiFetch('/api/weather/crawl/', { method: 'POST' });
      const json = await res.json();
      if (json.code === 0) {
        setStatusMsg(`爬取完成，保存 ${json.data?.saved_count ?? '?'} 条`);
        triggerRefresh(); // 刷新月份列表、数据
      } else {
        setStatusMsg(`爬取失败: ${json.message}`);
      }
    } catch {
      setStatusMsg('爬取请求异常');
    } finally {
      setCrawlLoading(false);
    }
  };

  /** 开始分析 */
  const handleAnalyze = async () => {
    setAnalyzeLoading(true);
    setStatusMsg('分析中...');
    try {
      const res = await apiFetch('/api/weather/analyze/', { method: 'POST' });
      const json = await res.json();
      if (json.code === 0) {
        setStatusMsg('分析完成');
        triggerRefresh();
      } else {
        setStatusMsg(`分析失败: ${json.message}`);
      }
    } catch {
      setStatusMsg('分析请求异常');
    } finally {
      setAnalyzeLoading(false);
    }
  };

  /** 爬取预报 */
  const handleForecast = async () => {
    setForecastLoading(true);
    setStatusMsg('预报爬取中...');
    try {
      const res = await apiFetch('/api/weather/forecast/fetch/', { method: 'POST' });
      const json = await res.json();
      if (json.code === 0) {
        setStatusMsg(`预报完成，${json.data?.count ?? '?'} 条`);
        triggerRefresh();
      } else {
        setStatusMsg(`预报爬取失败: ${json.message}`);
      }
    } catch {
      setStatusMsg('预报请求异常');
    } finally {
      setForecastLoading(false);
    }
  };

  return (
    <header className="w-full flex flex-wrap items-center justify-between gap-3">
      {/* Left Group */}
      <div className="flex items-center gap-4">
        <div className="flex flex-col gap-1">
          <h1 className="text-[20px] sm:text-[26px] font-semibold text-[#1C1C1E] tracking-[-0.01em]">
            🌿 都江堰天气可视化
          </h1>
          <p className="text-[11px] sm:text-xs text-[#8E8E93]">近12个月历史天气数据洞察</p>
        </div>
        {/* Auth area */}
        {user ? (
          <div className="flex items-center gap-2 ml-4">
            <span className="text-sm text-[#4A6FA5] font-medium">👤 {user.username}</span>
            <button onClick={logout}
              className="text-xs text-[#8E8E93] hover:text-[#E07A5F] transition-colors">
              退出
            </button>
          </div>
        ) : (
          <a href="/lauth/login/"
            className="ml-4 h-9 px-4 bg-white border border-[#E8E8E6] rounded-xl flex items-center gap-2 text-sm text-[#4A6FA5] hover:bg-[#FAFAF8] transition-colors no-underline">
            <User className="w-4 h-4" />
            登录
          </a>
        )}
      </div>

      {/* Right Group */}
      {loading ? (
        <div className="h-10 px-4 flex items-center">
          <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
          <span className="ml-2 text-sm text-[#8E8E93]">加载月份...</span>
        </div>
      ) : (
        <div className="flex items-center gap-3">
          {/* Month Selector */}
          <select
            value={selectedMonth}
            onChange={(e) => setSelectedMonth(e.target.value)}
            className="h-10 px-4 bg-white border border-[#E8E8E6] rounded-xl text-sm text-[#1C1C1E] cursor-pointer outline-none focus:border-[#4A6FA5]"
          >
            {availableMonths.map((m) => (
              <option key={m.value} value={m.value}>
                {m.label}
              </option>
            ))}
          </select>

          {/* Button - 一键爬取 */}
          <button
            onClick={handleCrawl}
            disabled={crawlLoading}
            className="h-10 px-5 bg-gradient-to-br from-[#4A6FA5] to-[#7FA3C1] rounded-xl flex items-center gap-2 hover:shadow-lg transition-shadow disabled:opacity-60"
          >
            {crawlLoading ? (
              <Loader2 className="w-4 h-4 text-white animate-spin" />
            ) : (
              <CloudDownload className="w-4 h-4 text-white" />
            )}
            <span className="text-sm font-medium text-white">
              {crawlLoading ? '爬取中...' : '一键爬取'}
            </span>
          </button>

          {/* Button - 开始分析 */}
          <button
            onClick={handleAnalyze}
            disabled={analyzeLoading}
            className="h-10 px-5 bg-white border border-[#E8E8E6] rounded-xl text-sm font-medium text-[#4A6FA5] hover:bg-[#FAFAF8] transition-colors disabled:opacity-60"
          >
            {analyzeLoading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                分析中...
              </span>
            ) : (
              '开始分析'
            )}
          </button>

          {/* Button - 爬取预报 */}
          <button
            onClick={handleForecast}
            disabled={forecastLoading}
            className="h-10 px-5 bg-white border border-[#E8E8E6] rounded-xl text-sm font-medium text-[#81B29A] hover:bg-[#FAFAF8] transition-colors disabled:opacity-60"
          >
            {forecastLoading ? (
              <span className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                预报中...
              </span>
            ) : (
              '40天预报'
            )}
          </button>

          {/* Status Badge */}
          <div className="h-6 px-2.5 bg-white border border-[#E8E8E6] rounded-xl flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                crawlLoading || analyzeLoading || forecastLoading ? 'bg-[#D4A373] animate-pulse' : 'bg-[#81B29A]'
              }`}
            ></span>
            <span className="text-xs text-[#8E8E93] truncate max-w-[120px]">{statusMsg}</span>
          </div>
        </div>
      )}
    </header>
  );
}
