import { Suspense, lazy } from 'react';
import { MonthProvider } from './context/MonthContext';
import Navbar from './components/Navbar';
import StatsGrid from './components/StatsGrid';
import ForecastRow from './components/ForecastRow';
import Footer from './components/Footer';

// 重型图表组件按需加载，减小首屏 bundle
const PrimaryCharts = lazy(() => import('./components/PrimaryCharts'));
const SecondaryCharts = lazy(() => import('./components/SecondaryCharts'));
const HeatmapChart = lazy(() => import('./components/HeatmapChart'));
const InsightAndTable = lazy(() => import('./components/InsightAndTable'));

/** 懒加载组件的骨架屏占位 */
function ChartSkeleton({ height = 'h-[400px]', label = '加载中...' }: { height?: string; label?: string }) {
  return (
    <div className={`w-full bg-white border border-[#E8E8E6] rounded-[20px] ${height} flex items-center justify-center shadow-[0_2px_12px_rgba(0,0,0,0.04)]`}>
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-[#4A6FA5] border-t-transparent rounded-full animate-spin"></div>
        <span className="text-sm text-[#8E8E93]">{label}</span>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <MonthProvider>
      <div className="min-h-screen bg-[#FAFAF8]">
        <div className="max-w-[1320px] mx-auto px-6 py-10 flex flex-col gap-6">
          {/* 01-Header / 顶部控制栏（同步加载） */}
          <Navbar />

          {/* 02-StatsGrid / 统计卡片 */}
          <StatsGrid />

          {/* 02.5-未来天气预报 */}
          <ForecastRow />

          {/* 03-PrimaryCharts / 主图表区（懒加载） */}
          <Suspense fallback={<ChartSkeleton label="加载图表..." />}>
            <PrimaryCharts />
          </Suspense>

          {/* 04-SecondaryCharts / 次图表区（懒加载） */}
          <Suspense fallback={<ChartSkeleton height="h-[320px]" label="加载图表..." />}>
            <SecondaryCharts />
          </Suspense>

          {/* 05-AdvancedChart / 热力图（懒加载） */}
          <Suspense fallback={<ChartSkeleton height="h-[320px]" label="加载热力图..." />}>
            <HeatmapChart />
          </Suspense>

          {/* 06-InsightTable / 建议与表格（懒加载） */}
          <Suspense fallback={<ChartSkeleton height="h-[400px]" label="加载数据表..." />}>
            <InsightAndTable />
          </Suspense>

          {/* 07-Footer / 页脚 */}
          <Footer />
        </div>
      </div>
    </MonthProvider>
  );
}
