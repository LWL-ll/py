const tableData = [
  { date: '2025-06-01', maxTemp: 28, minTemp: 19, weather: '晴', weatherType: 'sunny', wind: '微风' },
  { date: '2025-06-02', maxTemp: 26, minTemp: 18, weather: '阴', weatherType: 'overcast', wind: '2级' },
  { date: '2025-06-03', maxTemp: 24, minTemp: 17, weather: '雨', weatherType: 'rainy', wind: '3级' },
  { date: '2025-06-04', maxTemp: 27, minTemp: 20, weather: '晴', weatherType: 'sunny', wind: '微风' },
  { date: '2025-06-05', maxTemp: 29, minTemp: 21, weather: '晴', weatherType: 'sunny', wind: '2级' },
];

const WeatherPill = ({ weather, type }: { weather: string; type: string }) => {
  const styles = {
    sunny: { bg: '#D4A37326', border: '#D4A3734D', text: '#D4A373' },
    rainy: { bg: '#7FA3C126', border: '#7FA3C14D', text: '#7FA3C1' },
    overcast: { bg: '#A8A29E26', border: '#A8A29E4D', text: '#78716C' },
  };
  const style = styles[type as keyof typeof styles] || styles.overcast;

  return (
    <span
      className="inline-block px-3 py-1 rounded-full text-xs font-medium"
      style={{
        backgroundColor: style.bg,
        border: `1px solid ${style.border}`,
        color: style.text,
      }}
    >
      {weather}
    </span>
  );
};

export default function InsightAndTable() {
  return (
    <div className="w-full flex flex-col lg:flex-row gap-6">
      {/* Left Card - Clothing Advice (1/3 width) */}
      <div className="flex-1 lg:max-w-[33%] bg-gradient-to-br from-[#F5F5F0] to-[#FAFAF8] border border-[#E8E8E6] rounded-[20px] p-7 shadow-[0_2px_12px_rgba(0,0,0,0.04),0_0_0_1px_rgba(0,0,0,0.02)]">
        <h3 className="text-lg font-semibold text-[#1C1C1E] mb-4">🧥 智能穿衣建议</h3>

        <div className="text-[40px] text-[#D4A373] mb-4 leading-none">"</div>

        <p className="text-[15px] text-[#4A4A4A] leading-relaxed mb-4">
          春秋舒适，建议穿着T恤搭配薄外套。雨天概率较高，建议随身携带雨具。
        </p>

        <div className="flex gap-2">
          <span
            className="px-3 py-1.5 rounded-full text-xs font-medium"
            style={{ backgroundColor: '#D4A37326', color: '#D4A373' }}
          >
            薄外套
          </span>
          <span
            className="px-3 py-1.5 rounded-full text-xs font-medium"
            style={{ backgroundColor: '#7FA3C126', color: '#7FA3C1' }}
          >
            雨具
          </span>
        </div>
      </div>

      {/* Right Card - Weather Table (2/3 width) */}
      <div className="flex-[2] bg-white border border-[#E8E8E6] rounded-[20px] overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.04),0_0_0_1px_rgba(0,0,0,0.02)]">
        <div className="px-6 py-4">
          <h3 className="text-lg font-semibold text-[#1C1C1E]">📋 当月天气明细</h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-[#F5F5F0] h-12">
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">日期</th>
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">最高温(°C)</th>
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">最低温(°C)</th>
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">天气状况</th>
                <th className="px-4 text-center text-[13px] font-semibold text-[#6E6E73] uppercase tracking-wide">风力</th>
              </tr>
            </thead>
            <tbody>
              {tableData.map((row, index) => (
                <tr
                  key={row.date}
                  className={`h-[52px] hover:bg-[#FAFAF8] transition-colors ${
                    index % 2 === 0 ? 'bg-white' : 'bg-[#FAFAF8]'
                  }`}
                >
                  <td className="px-4 text-center text-sm text-[#4A4A4A]">{row.date}</td>
                  <td className="px-4 text-center text-sm text-[#4A4A4A]">{row.maxTemp}</td>
                  <td className="px-4 text-center text-sm text-[#4A4A4A]">{row.minTemp}</td>
                  <td className="px-4 text-center">
                    <WeatherPill weather={row.weather} type={row.weatherType} />
                  </td>
                  <td className="px-4 text-center text-sm text-[#4A4A4A]">{row.wind}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="h-12 flex items-center justify-center gap-2 border-t border-[#E8E8E6]">
          <button className="w-6 h-6 rounded-full flex items-center justify-center text-[13px] text-[#8E8E93] hover:bg-[#FAFAF8]">
            ‹
          </button>
          <button className="w-6 h-6 rounded-full flex items-center justify-center text-[13px] bg-[#4A6FA5] text-white">
            1
          </button>
          <button className="w-6 h-6 rounded-full flex items-center justify-center text-[13px] text-[#8E8E93] hover:bg-[#FAFAF8]">
            2
          </button>
          <button className="w-6 h-6 rounded-full flex items-center justify-center text-[13px] text-[#8E8E93] hover:bg-[#FAFAF8]">
            3
          </button>
          <button className="w-6 h-6 rounded-full flex items-center justify-center text-[13px] text-[#8E8E93] hover:bg-[#FAFAF8]">
            ›
          </button>
        </div>
      </div>
    </div>
  );
}
