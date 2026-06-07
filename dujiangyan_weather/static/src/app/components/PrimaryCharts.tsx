import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const tempData = [
  { day: '1日', maxTemp: 18, minTemp: 12 },
  { day: '5日', maxTemp: 22, minTemp: 15 },
  { day: '10日', maxTemp: 26, minTemp: 18 },
  { day: '15日', maxTemp: 28, minTemp: 20 },
  { day: '20日', maxTemp: 30, minTemp: 22 },
  { day: '25日', maxTemp: 29, minTemp: 21 },
  { day: '30日', maxTemp: 27, minTemp: 19 },
];

const weatherData = [
  { name: '晴天', value: 65, color: '#D4A373' },
  { name: '雨天', value: 20, color: '#7FA3C1' },
  { name: '多云', value: 10, color: '#A8A29E' },
  { name: '阴天', value: 5, color: '#78716C' },
];

export default function PrimaryCharts() {
  return (
    <div className="w-full flex flex-col lg:flex-row gap-6">
      {/* Left Chart Card - Temperature Trend (2/3 width) */}
      <div className="flex-[2] bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04),0_0_0_1px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">月度温度变化趋势</h3>
        </div>
        <div className="bg-[#FAFAF8] rounded-xl p-4 h-[320px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={tempData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E8E8E6" vertical={false} />
              <XAxis dataKey="day" stroke="#8E8E93" style={{ fontSize: '12px' }} />
              <YAxis stroke="#8E8E93" style={{ fontSize: '12px' }} />
              <Tooltip />
              <defs>
                <linearGradient id="hotGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#E07A5F" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#E07A5F" stopOpacity={0}/>
                </linearGradient>
                <linearGradient id="coldGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#7FA3C1" stopOpacity={0.3}/>
                  <stop offset="95%" stopColor="#7FA3C1" stopOpacity={0}/>
                </linearGradient>
              </defs>
              <Line
                type="monotone"
                dataKey="maxTemp"
                stroke="#E07A5F"
                strokeWidth={3}
                dot={{ fill: '#E07A5F', r: 4 }}
                fill="url(#hotGradient)"
                name="最高温"
              />
              <Line
                type="monotone"
                dataKey="minTemp"
                stroke="#7FA3C1"
                strokeWidth={3}
                dot={{ fill: '#7FA3C1', r: 4 }}
                fill="url(#coldGradient)"
                name="最低温"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Right Chart Card - Weather Distribution (1/3 width) */}
      <div className="flex-1 bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04),0_0_0_1px_rgba(0,0,0,0.02)]">
        <div className="flex items-center gap-2 mb-4">
          <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
          <h3 className="text-lg font-semibold text-[#1C1C1E]">天气状况分布</h3>
        </div>
        <div className="flex flex-col items-center gap-4">
          <div className="relative w-[200px] h-[200px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={weatherData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={90}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {weatherData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-lg font-bold text-[#1C1C1E]">365天</span>
            </div>
          </div>
          <div className="flex flex-col gap-2 w-full">
            {weatherData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></div>
                <span className="text-[13px] text-[#6E6E73]">{item.name}</span>
                <span className="ml-auto text-[13px] font-medium text-[#1C1C1E]">{item.value}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
