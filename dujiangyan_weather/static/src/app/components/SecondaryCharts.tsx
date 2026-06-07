import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

const rainyDaysData = [
  { month: '1月', days: 5 },
  { month: '2月', days: 7 },
  { month: '3月', days: 12 },
  { month: '4月', days: 15 },
  { month: '5月', days: 18 },
  { month: '6月', days: 20 },
  { month: '7月', days: 22 },
  { month: '8月', days: 19 },
  { month: '9月', days: 14 },
  { month: '10月', days: 10 },
  { month: '11月', days: 7 },
  { month: '12月', days: 4 },
];

const climateData = [
  { category: '温度舒适度', value: 85 },
  { category: '湿度适宜度', value: 70 },
  { category: '日照充足度', value: 75 },
  { category: '空气质量', value: 90 },
  { category: '降水适中度', value: 65 },
];

export default function SecondaryCharts() {
  return (
    <div className="w-full flex flex-col lg:flex-row gap-6">
      {/* Left Card - Monthly Rain Days */}
      <div className="flex-1 bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04),0_0_0_1px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">月度降雨天数统计</h3>
        </div>
        <div className="bg-[#FAFAF8] rounded-xl p-4 h-[240px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={rainyDaysData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F5F5F0" vertical={false} />
              <XAxis dataKey="month" stroke="#8E8E93" style={{ fontSize: '11px' }} />
              <YAxis stroke="#8E8E93" style={{ fontSize: '11px' }} />
              <Tooltip />
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#4A6FA5" />
                  <stop offset="100%" stopColor="#7FA3C1" />
                </linearGradient>
              </defs>
              <Bar dataKey="days" fill="url(#barGradient)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Right Card - Climate Score Radar */}
      <div className="flex-1 bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04),0_0_0_1px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">气候综合评分</h3>
        </div>
        <div className="bg-[#FAFAF8] rounded-xl p-4 h-[240px] flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%">
            <RadarChart data={climateData}>
              <PolarGrid stroke="#E8E8E6" />
              <PolarAngleAxis dataKey="category" stroke="#8E8E93" style={{ fontSize: '11px' }} />
              <PolarRadiusAxis stroke="#8E8E93" style={{ fontSize: '10px' }} />
              <Radar
                name="评分"
                dataKey="value"
                stroke="#4A6FA5"
                fill="#4A6FA5"
                fillOpacity={0.15}
                strokeWidth={2}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
