import { CloudDownload } from 'lucide-react';

export default function Navbar() {
  return (
    <header className="w-full h-[72px] flex items-center justify-between">
      {/* Left Group */}
      <div className="flex flex-col gap-1">
        <h1 className="text-[26px] font-semibold text-[#1C1C1E] tracking-[-0.01em]">
          🌿 都江堰天气可视化系统
        </h1>
        <p className="text-xs text-[#8E8E93]">近12个月历史天气数据洞察</p>
      </div>

      {/* Right Group */}
      <div className="flex items-center gap-3">
        {/* Month Selector */}
        <div className="h-10 px-4 bg-white border border-[#E8E8E6] rounded-xl flex items-center">
          <span className="text-sm text-[#1C1C1E]">2025-06 ▼</span>
        </div>

        {/* Button - 一键爬取 */}
        <button className="h-10 px-5 bg-gradient-to-br from-[#4A6FA5] to-[#7FA3C1] rounded-xl flex items-center gap-2 hover:shadow-lg transition-shadow">
          <CloudDownload className="w-4 h-4 text-white" />
          <span className="text-sm font-medium text-white">一键爬取</span>
        </button>

        {/* Button - 开始分析 */}
        <button className="h-10 px-5 bg-white border border-[#E8E8E6] rounded-xl text-sm font-medium text-[#4A6FA5] hover:bg-[#FAFAF8] transition-colors">
          开始分析
        </button>

        {/* Status Badge */}
        <div className="h-6 px-2.5 bg-white border border-[#E8E8E6] rounded-xl flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-[#81B29A]"></span>
          <span className="text-xs text-[#8E8E93]">系统就绪</span>
        </div>
      </div>
    </header>
  );
}
