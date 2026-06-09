import { Suspense, lazy, useEffect } from 'react';
import { Loader2 } from 'lucide-react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { MonthProvider } from './context/MonthContext';
import Navbar from './components/Navbar';
import StatsGrid from './components/StatsGrid';
import ForecastRow from './components/ForecastRow';
import Footer from './components/Footer';
import AIChat from './components/AIChat';

const PrimaryCharts = lazy(() => import('./components/PrimaryCharts'));
const SecondaryCharts = lazy(() => import('./components/SecondaryCharts'));
const HeatmapChart = lazy(() => import('./components/HeatmapChart'));
const InsightAndTable = lazy(() => import('./components/InsightAndTable'));

function ChartSkeleton({ height = 'h-[400px]', label = '加载中...' }: { height?: string; label?: string }) {
  return (
    <div className={`w-full bg-white border border-[#E8E8E6] rounded-[20px] ${height} flex items-center justify-center shadow-[0_2px_12px_rgba(0,0,0,0.04)] animate-fadeInUp`}>
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-[#4A6FA5] border-t-transparent rounded-full animate-spin"></div>
        <span className="text-sm text-[#8E8E93]">{label}</span>
      </div>
    </div>
  );
}

function Dashboard() {
  return (
    <MonthProvider>
      <div className="min-h-screen bg-[#FAFAF8] animate-fadeIn">
        <div className="max-w-[1320px] mx-auto px-6 py-10 flex flex-col gap-6">
          <div className="animate-fadeInUp" style={{ animationDelay: '0s' }}><Navbar /></div>
          <div className="animate-fadeInUp" style={{ animationDelay: '0.1s' }}><StatsGrid /></div>
          <div className="animate-fadeInUp" style={{ animationDelay: '0.15s' }}><ForecastRow /></div>
          <div className="animate-fadeInUp" style={{ animationDelay: '0.2s' }}>
            <Suspense fallback={<ChartSkeleton label="加载图表..." />}><PrimaryCharts /></Suspense>
          </div>
          <div className="animate-fadeInUp" style={{ animationDelay: '0.25s' }}>
            <Suspense fallback={<ChartSkeleton height="h-[320px]" label="加载图表..." />}><SecondaryCharts /></Suspense>
          </div>
          <div className="animate-fadeInUp" style={{ animationDelay: '0.3s' }}>
            <Suspense fallback={<ChartSkeleton height="h-[320px]" label="加载热力图..." />}><HeatmapChart /></Suspense>
          </div>
          <div className="animate-fadeInUp" style={{ animationDelay: '0.35s' }}>
            <Suspense fallback={<ChartSkeleton height="h-[400px]" label="加载数据表..." />}><InsightAndTable /></Suspense>
          </div>
          <div className="animate-fadeInUp" style={{ animationDelay: '0.4s' }}><Footer /></div>
        </div>
        <AIChat />
      </div>
    </MonthProvider>
  );
}

function AppContent() {
  const { user, loading } = useAuth();

  useEffect(() => {
    if (!loading && !user) {
      window.location.href = '/lauth/login/';
    }
  }, [loading, user]);

  if (loading || !user) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-[#4A6FA5] to-[#7FA3C1] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="text-5xl">🌿</div>
          <Loader2 className="w-8 h-8 animate-spin text-white" />
          <span className="text-white/80 text-sm">加载中...</span>
        </div>
      </div>
    );
  }

  return <Dashboard />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
