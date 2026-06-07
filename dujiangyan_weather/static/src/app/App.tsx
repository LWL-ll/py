import { MonthProvider } from './context/MonthContext';
import Navbar from './components/Navbar';
import StatsGrid from './components/StatsGrid';
import PrimaryCharts from './components/PrimaryCharts';
import SecondaryCharts from './components/SecondaryCharts';
import HeatmapChart from './components/HeatmapChart';
import InsightAndTable from './components/InsightAndTable';
import Footer from './components/Footer';

export default function App() {
  return (
    <MonthProvider>
      <div className="min-h-screen bg-[#FAFAF8]">
        {/* Main Container / 主容器 */}
        <div className="max-w-[1320px] mx-auto px-6 py-10 flex flex-col gap-6">
          {/* 01-Header / 顶部控制栏 */}
          <Navbar />

          {/* 02-StatsGrid / 统计卡片 */}
          <StatsGrid />

          {/* 03-PrimaryCharts / 主图表区 */}
          <PrimaryCharts />

          {/* 04-SecondaryCharts / 次图表区 */}
          <SecondaryCharts />

          {/* 05-AdvancedChart / 热力图 */}
          <HeatmapChart />

          {/* 06-InsightTable / 建议与表格 */}
          <InsightAndTable />

          {/* 07-Footer / 页脚 */}
          <Footer />
        </div>
      </div>
    </MonthProvider>
  );
}
