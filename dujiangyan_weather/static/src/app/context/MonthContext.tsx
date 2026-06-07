import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';

/** 可用月份项 */
interface MonthOption {
  label: string;
  value: string;
  year: number;
  month: number;
}

/** Context 暴露的值 */
interface MonthContextType {
  selectedMonth: string;             // 当前选中月份 "YYYY-MM"
  setSelectedMonth: (m: string) => void;
  availableMonths: MonthOption[];
  loading: boolean;
  refreshKey: number;
  triggerRefresh: () => void;
}

const MonthContext = createContext<MonthContextType | null>(null);

export function MonthProvider({ children }: { children: ReactNode }) {
  const [selectedMonth, setSelectedMonth] = useState('');
  const [availableMonths, setAvailableMonths] = useState<MonthOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshKey, setRefreshKey] = useState(0);

  // 从后端获取可用月份列表
  const fetchMonths = useCallback(() => {
    setLoading(true);
    fetch('/api/weather/months/')
      .then((res) => res.json())
      .then((json) => {
        if (json.data?.length) {
          setAvailableMonths(json.data);
          // 若未选中，默认选第一个（最新月份）
          setSelectedMonth((prev) => prev || json.data[0].value);
        }
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    fetchMonths();
  }, [fetchMonths, refreshKey]);

  const triggerRefresh = () => {
    setRefreshKey((k) => k + 1);
  };

  return (
    <MonthContext.Provider
      value={{ selectedMonth, setSelectedMonth, availableMonths, loading, refreshKey, triggerRefresh }}
    >
      {children}
    </MonthContext.Provider>
  );
}

/** 便捷 hook，任何子组件直接获取月份上下文 */
export function useMonth() {
  const ctx = useContext(MonthContext);
  if (!ctx) {
    throw new Error('useMonth 必须在 MonthProvider 内使用');
  }
  return ctx;
}
