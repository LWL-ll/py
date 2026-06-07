export default function HeatmapChart() {
  // Generate heatmap data: 12 months × 5 rows
  const months = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月'];
  const heatmapData = months.map((month, monthIndex) => {
    return Array.from({ length: 5 }, (_, rowIndex) => {
      // Generate temperature values (higher in summer months)
      const baseTemp = 15 + Math.sin((monthIndex / 12) * Math.PI * 2) * 10;
      const variation = Math.random() * 5;
      const temp = baseTemp + variation + rowIndex * 2;
      return { month, row: rowIndex, temp: Math.round(temp) };
    });
  }).flat();

  const getHeatColor = (temp: number) => {
    if (temp < 15) return '#7FA3C1'; // Cold - misty blue
    if (temp < 20) return '#81B29A'; // Mild - sage green
    if (temp < 25) return '#D4A373'; // Warm - terracotta amber
    return '#E07A5F'; // Hot - terra cotta
  };

  return (
    <div className="w-full bg-white border border-[#E8E8E6] rounded-[20px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.04),0_0_0_1px_rgba(0,0,0,0.02)]">
      <div className="flex items-center gap-2 mb-4">
        <span className="w-2 h-2 rounded-full bg-[#4A6FA5]"></span>
        <h3 className="text-lg font-semibold text-[#1C1C1E]">年度温度热力分布</h3>
      </div>
      <div className="bg-[#FAFAF8] rounded-xl p-6">
        <div className="grid grid-cols-12 gap-2 mb-4">
          {months.map((month, monthIndex) => (
            <div key={month} className="flex flex-col gap-1">
              {Array.from({ length: 5 }).map((_, rowIndex) => {
                const dataPoint = heatmapData.find(
                  (d) => d.month === month && d.row === rowIndex
                );
                return (
                  <div
                    key={`${monthIndex}-${rowIndex}`}
                    className="w-full aspect-square rounded-md transition-transform hover:scale-110 cursor-pointer"
                    style={{ backgroundColor: getHeatColor(dataPoint?.temp || 20) }}
                    title={`${month} - ${dataPoint?.temp}°C`}
                  ></div>
                );
              })}
              <span className="text-[10px] text-[#8E8E93] text-center mt-1">{month}</span>
            </div>
          ))}
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 mt-4 pt-4 border-t border-[#E8E8E6]">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#7FA3C1]"></div>
            <span className="text-xs text-[#6E6E73]">偏冷</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#81B29A]"></div>
            <span className="text-xs text-[#6E6E73]">舒适</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-[#E07A5F]"></div>
            <span className="text-xs text-[#6E6E73]">偏热</span>
          </div>
        </div>
      </div>
    </div>
  );
}
