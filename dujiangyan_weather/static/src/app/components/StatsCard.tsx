import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  icon: LucideIcon;
  label: string;
  value: string;
  accentColor: string;
  sparklineColor: string;
}

export default function StatsCard({ icon: Icon, label, value, accentColor, sparklineColor }: StatsCardProps) {
  return (
    <div className="bg-white border border-[#E8E8E6] rounded-[20px] p-5 sm:p-7 min-w-[160px] sm:min-w-[220px] flex-1 flex flex-col gap-3 sm:gap-4 shadow-[0_2px_12px_rgba(0,0,0,0.04),0_0_0_1px_rgba(0,0,0,0.02)] hover-lift">
      {/* Icon Circle */}
      <div
        className="w-10 h-10 rounded-full flex items-center justify-center"
        style={{ backgroundColor: `${accentColor}26` }}
      >
        <Icon className="w-5 h-5" style={{ color: accentColor }} />
      </div>

      {/* Label */}
      <span className="text-xs font-medium text-[#8E8E93] uppercase tracking-wider">{label}</span>

      {/* Value */}
      <span className="text-[28px] sm:text-[40px] font-bold text-[#1C1C1E] tabular-nums leading-none">{value}</span>

      {/* Sparkline Area */}
      <div
        className="w-[120px] h-8 rounded-md relative overflow-hidden"
        style={{ backgroundColor: `${sparklineColor}1A` }}
      >
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 120 32" preserveAspectRatio="none">
          <path
            d="M 0,20 Q 20,10 40,15 T 80,12 T 120,8"
            fill="none"
            stroke={sparklineColor}
            strokeWidth="2"
            vectorEffect="non-scaling-stroke"
          />
        </svg>
      </div>
    </div>
  );
}
