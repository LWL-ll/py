import { Sun, CloudRain, ThermometerSun, ThermometerSnowflake } from 'lucide-react';
import StatsCard from './StatsCard';

export default function StatsGrid() {
  return (
    <div className="w-full flex flex-wrap gap-4">
      <StatsCard
        icon={Sun}
        label="晴天概率"
        value="65%"
        accentColor="#D4A373"
        sparklineColor="#D4A373"
      />
      <StatsCard
        icon={CloudRain}
        label="雨天概率"
        value="20%"
        accentColor="#7FA3C1"
        sparklineColor="#7FA3C1"
      />
      <StatsCard
        icon={ThermometerSun}
        label="月均最高温"
        value="28°C"
        accentColor="#E07A5F"
        sparklineColor="#E07A5F"
      />
      <StatsCard
        icon={ThermometerSnowflake}
        label="月均最低温"
        value="19°C"
        accentColor="#81B29A"
        sparklineColor="#81B29A"
      />
    </div>
  );
}
