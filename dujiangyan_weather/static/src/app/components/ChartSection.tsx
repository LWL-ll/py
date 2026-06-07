import { PieChart, Pie, Cell, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const weatherData = [
  { name: '晴天', value: 65, color: '#F59E0B' },
  { name: '多云', value: 15, color: '#94A3B8' },
  { name: '雨天', value: 20, color: '#3B82F6' },
];

const tempData = [
  { month: '1日', maxTemp: 18, minTemp: 12 },
  { month: '5日', maxTemp: 22, minTemp: 15 },
  { month: '10日', maxTemp: 26, minTemp: 18 },
  { month: '15日', maxTemp: 28, minTemp: 20 },
  { month: '20日', maxTemp: 30, minTemp: 22 },
  { month: '25日', maxTemp: 29, minTemp: 21 },
  { month: '30日', maxTemp: 27, minTemp: 19 },
];

export default function ChartSection() {
  return (
    <div className="w-full grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Weather Distribution Chart */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-4">天气状况分布</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={weatherData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={5}
              dataKey="value"
            >
              {weatherData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
        <div className="flex justify-center gap-6 mt-4">
          {weatherData.map((item) => (
            <div key={item.name} className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }}></div>
              <span className="text-sm text-slate-600">{item.name}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Temperature Trend Chart */}
      <div className="bg-white rounded-xl p-6 shadow-sm">
        <h3 className="text-lg font-bold text-slate-900 mb-4">月度温度趋势</h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={tempData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
            <XAxis dataKey="month" stroke="#64748B" style={{ fontSize: '12px' }} />
            <YAxis stroke="#64748B" style={{ fontSize: '12px' }} label={{ value: '温度 (°C)', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="maxTemp"
              stroke="#EF4444"
              strokeWidth={3}
              dot={{ fill: '#EF4444', r: 4 }}
              name="最高温"
            />
            <Line
              type="monotone"
              dataKey="minTemp"
              stroke="#0EA5E9"
              strokeWidth={3}
              dot={{ fill: '#0EA5E9', r: 4 }}
              name="最低温"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
