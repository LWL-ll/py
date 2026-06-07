import { Shirt } from 'lucide-react';

export default function AdviceCard() {
  return (
    <div className="w-full bg-[#E0F2FE] rounded-xl p-6 flex gap-4">
      <Shirt className="w-12 h-12 text-[#0EA5E9] flex-shrink-0" />
      <div className="flex flex-col gap-2">
        <h3 className="text-lg font-bold text-[#1E3A8A]">🧥 智能穿衣建议</h3>
        <p className="text-[#334155] leading-relaxed">
          春秋舒适，建议穿着T恤搭配薄外套。当月雨天概率较高，建议随身携带雨具。
        </p>
      </div>
    </div>
  );
}
