import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Loader2, Sparkles } from 'lucide-react';
import { useMonth } from '../context/MonthContext';

interface Msg {
  role: 'user' | 'ai';
  text: string;
}

export default function AIChat() {
  const { selectedMonth } = useMonth();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<Msg[]>([
    { role: 'ai', text: '你好！我是小堰 🌿\n都江堰天气助手。\n问我任何天气相关问题吧～' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    const q = input.trim();
    if (!q || loading) return;

    setMessages((prev) => [...prev, { role: 'user', text: q }]);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch('/api/weather/ai-chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrfToken() },
        body: JSON.stringify({ question: q, month: selectedMonth }),
      });
      const json = await res.json();
      const answer = json.data?.answer || '抱歉，AI 暂时无法回答，请稍后再试。';
      setMessages((prev) => [...prev, { role: 'ai', text: answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: 'ai', text: '网络错误，请稍后再试。' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      {/* 浮动按钮 */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 right-6 z-50 w-14 h-14 bg-gradient-to-br from-[#4A6FA5] to-[#7FA3C1] rounded-2xl shadow-lg hover:shadow-xl hover:-translate-y-1 transition-all flex items-center justify-center animate-fadeInUp"
        >
          <MessageCircle className="w-6 h-6 text-white" />
        </button>
      )}

      {/* 聊天窗口 */}
      {open && (
        <div className="fixed bottom-6 right-6 z-50 w-[380px] max-w-[90vw] h-[520px] max-h-[70vh] bg-white rounded-2xl shadow-2xl border border-[#E8E8E6] flex flex-col animate-fadeInUp overflow-hidden">
          {/* Header */}
          <div className="h-14 px-4 bg-gradient-to-r from-[#4A6FA5] to-[#7FA3C1] flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-white" />
              <span className="text-white font-medium text-sm">小堰 · AI 天气助手</span>
            </div>
            <button onClick={() => setOpen(false)} className="p-1 rounded-lg hover:bg-white/20 transition-colors">
              <X className="w-5 h-5 text-white" />
            </button>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 bg-[#FAFAF8]">
            {messages.map((msg, i) => (
              <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-[85%] px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === 'user'
                    ? 'bg-[#4A6FA5] text-white rounded-br-md'
                    : 'bg-white border border-[#E8E8E6] text-[#4A4A4A] rounded-bl-md'
                }`}>
                  {msg.text}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-[#E8E8E6] rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-2">
                  <Loader2 className="w-4 h-4 animate-spin text-[#8E8E93]" />
                  <span className="text-sm text-[#8E8E93]">思考中...</span>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {/* Input */}
          <div className="p-3 border-t border-[#E8E8E6] flex gap-2 bg-white shrink-0">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="问小堰任何天气问题..."
              className="flex-1 h-10 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]"
            />
            <button
              onClick={handleSend}
              disabled={loading || !input.trim()}
              className="h-10 w-10 bg-[#4A6FA5] rounded-xl flex items-center justify-center disabled:opacity-40 hover:bg-[#3D5A8A] transition-colors"
            >
              <Send className="w-4 h-4 text-white" />
            </button>
          </div>
        </div>
      )}
    </>
  );
}

/** 读取 CSRF Cookie */
function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}
