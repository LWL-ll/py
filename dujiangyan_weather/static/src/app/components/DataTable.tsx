const tableData = [
  { date: '2025-06-01', maxTemp: 28, minTemp: 19, weather: '晴天', wind: '微风' },
  { date: '2025-06-02', maxTemp: 26, minTemp: 18, weather: '多云', wind: '2级' },
  { date: '2025-06-03', maxTemp: 24, minTemp: 17, weather: '小雨', wind: '3级' },
  { date: '2025-06-04', maxTemp: 27, minTemp: 20, weather: '晴天', wind: '微风' },
  { date: '2025-06-05', maxTemp: 29, minTemp: 21, weather: '晴天', wind: '2级' },
];

export default function DataTable() {
  return (
    <div className="w-full bg-white rounded-xl overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="bg-[#1E3A8A] text-white h-12">
              <th className="px-4 text-center font-bold text-sm">日期</th>
              <th className="px-4 text-center font-bold text-sm">最高温(°C)</th>
              <th className="px-4 text-center font-bold text-sm">最低温(°C)</th>
              <th className="px-4 text-center font-bold text-sm">天气状况</th>
              <th className="px-4 text-center font-bold text-sm">风力</th>
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, index) => (
              <tr
                key={row.date}
                className={`h-12 hover:bg-[#EFF6FF] transition-colors ${
                  index % 2 === 0 ? 'bg-white' : 'bg-[#F1F5F9]'
                }`}
              >
                <td className="px-4 text-center text-sm text-[#334155]">{row.date}</td>
                <td className="px-4 text-center text-sm text-[#334155]">{row.maxTemp}</td>
                <td className="px-4 text-center text-sm text-[#334155]">{row.minTemp}</td>
                <td className="px-4 text-center text-sm text-[#334155]">{row.weather}</td>
                <td className="px-4 text-center text-sm text-[#334155]">{row.wind}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {tableData.length === 0 && (
        <div className="py-12 text-center text-slate-500">
          暂无数据，请先点击'一键爬取'
        </div>
      )}
    </div>
  );
}
