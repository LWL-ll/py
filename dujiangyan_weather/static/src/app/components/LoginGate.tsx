import { useState } from 'react';
import { Loader2, Cloud, TrendingUp, Umbrella } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

/** 全屏登录页面——未登录时的入口 */
export default function LoginGate() {
  const { login, register, sendCode, sendResetCode, resetPassword } = useAuth();
  const [tab, setTab] = useState<'login' | 'register' | 'forgot'>('login');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [msgType, setMsgType] = useState<'error' | 'success'>('error');

  // 表单
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);

  const showMsg = (m: string, t: 'error' | 'success') => { setMsg(m); setMsgType(t); };

  const handleSendCode = async () => {
    if (!email) return showMsg('请输入邮箱', 'error');
    setLoading(true);
    const r = await sendCode(email);
    showMsg(r.message, r.ok ? 'success' : 'error');
    if (r.ok) setCodeSent(true);
    setLoading(false);
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) return showMsg('请填写邮箱和密码', 'error');
    setLoading(true);
    const r = await login(email, password);
    if (!r.ok) showMsg(r.message, 'error');
    setLoading(false);
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !email || !password || !code) return showMsg('请填写所有字段', 'error');
    if (username.length < 3) return showMsg('用户名至少3个字符', 'error');
    if (password.length < 6) return showMsg('密码至少6个字符', 'error');
    setLoading(true);
    const r = await register(username, email, password, code);
    if (!r.ok) showMsg(r.message, 'error');
    setLoading(false);
  };

  const handleSendReset = async () => {
    if (!email) return showMsg('请输入邮箱', 'error');
    setLoading(true);
    const r = await sendResetCode(email);
    showMsg(r.message, r.ok ? 'success' : 'error');
    if (r.ok) setCodeSent(true);
    setLoading(false);
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !code || !password) return showMsg('请填写所有字段', 'error');
    if (password.length < 6) return showMsg('新密码至少6个字符', 'error');
    setLoading(true);
    const r = await resetPassword(email, code, password);
    showMsg(r.message, r.ok ? 'success' : 'error');
    if (r.ok) setTimeout(() => { setTab('login'); setMsg(''); }, 1500);
    setLoading(false);
  };

  // 装饰性浮动图标
  const FloatIcon = ({ icon: Icon, className }: { icon: typeof Cloud; className: string }) => (
    <div className={`absolute opacity-10 animate-float ${className}`}>
      <Icon className="w-16 h-16" />
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#4A6FA5] via-[#7FA3C1] to-[#81B29A] flex items-center justify-center p-6 relative overflow-hidden">
      {/* 装饰浮动图标 */}
      <FloatIcon icon={Cloud} className="top-10 left-10" />
      <FloatIcon icon={TrendingUp} className="top-20 right-20" />
      <FloatIcon icon={Umbrella} className="bottom-20 left-20" />
      <Cloud className="absolute bottom-10 right-10 w-12 h-12 opacity-10 animate-float" style={{ animationDelay: '1s' }} />

      {/* 主卡片 */}
      <div className="relative z-10 bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl w-[420px] max-w-[95vw] p-8 animate-fadeInUp">
        {/* Logo */}
        <div className="text-center mb-6">
          <div className="text-5xl mb-3">🌿</div>
          <h1 className="text-2xl font-bold text-[#1C1C1E]">都江堰天气分析</h1>
          <p className="text-sm text-[#8E8E93] mt-1">历史数据洞察 · 智能生活建议</p>
        </div>

        {/* Tabs */}
        <div className="flex bg-[#FAFAF8] rounded-xl p-1 mb-6">
          {([
            ['login', '登录'],
            ['register', '注册'],
            ['forgot', '找回密码'],
          ] as const).map(([k, v]) => (
            <button
              key={k}
              onClick={() => { setTab(k); setMsg(''); setCodeSent(false); }}
              className={`flex-1 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                tab === k ? 'bg-white text-[#4A6FA5] shadow-sm' : 'text-[#8E8E93] hover:text-[#4A6FA5]'
              }`}
            >
              {v}
            </button>
          ))}
        </div>

        {/* Message */}
        {msg && (
          <div className={`mb-4 px-4 py-2.5 rounded-xl text-xs animate-fadeIn ${
            msgType === 'error' ? 'bg-[#E07A5F15] text-[#E07A5F] border border-[#E07A5F20]' :
            'bg-[#81B29A15] text-[#81B29A] border border-[#81B29A20]'
          }`}>
            {msg}
          </div>
        )}

        {/* Forms */}
        {tab === 'login' && (
          <form onSubmit={handleLogin} className="flex flex-col gap-3 animate-fadeIn">
            <input type="email" placeholder="邮箱地址" value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5] focus:bg-white transition-all" />
            <input type="password" placeholder="密码" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5] focus:bg-white transition-all" />
            <button type="submit" disabled={loading}
              className="h-12 bg-gradient-to-r from-[#4A6FA5] to-[#7FA3C1] text-white rounded-xl text-sm font-medium hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-60 flex items-center justify-center">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : '登 录'}
            </button>
          </form>
        )}

        {tab === 'register' && (
          <form onSubmit={handleRegister} className="flex flex-col gap-3 animate-fadeIn">
            <input type="text" placeholder="用户名（至少3个字符）" value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5] focus:bg-white transition-all" />
            <div className="flex gap-2">
              <input type="email" placeholder="邮箱地址" value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5] focus:bg-white transition-all" />
              <button type="button" onClick={handleSendCode} disabled={loading}
                className="h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-xs text-[#4A6FA5] hover:bg-[#F0F0EB] transition-colors whitespace-nowrap disabled:opacity-60">
                {codeSent ? '✓ 已发送' : '发送验证码'}
              </button>
            </div>
            <input type="text" placeholder="验证码（6位数字）" value={code} maxLength={6}
              onChange={(e) => setCode(e.target.value)}
              className="h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5] focus:bg-white transition-all" />
            <input type="password" placeholder="密码（至少6个字符）" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5] focus:bg-white transition-all" />
            <button type="submit" disabled={loading}
              className="h-12 bg-gradient-to-r from-[#81B29A] to-[#6A9A7F] text-white rounded-xl text-sm font-medium hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-60 flex items-center justify-center">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : '注 册'}
            </button>
          </form>
        )}

        {tab === 'forgot' && (
          <form onSubmit={handleReset} className="flex flex-col gap-3 animate-fadeIn">
            <div className="flex gap-2">
              <input type="email" placeholder="注册邮箱" value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5] focus:bg-white transition-all" />
              <button type="button" onClick={handleSendReset} disabled={loading}
                className="h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-xs text-[#4A6FA5] hover:bg-[#F0F0EB] transition-colors whitespace-nowrap disabled:opacity-60">
                {codeSent ? '✓ 已发送' : '发送验证码'}
              </button>
            </div>
            <input type="text" placeholder="验证码（6位数字）" value={code} maxLength={6}
              onChange={(e) => setCode(e.target.value)}
              className="h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5] focus:bg-white transition-all" />
            <input type="password" placeholder="新密码（至少6个字符）" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-12 px-4 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5] focus:bg-white transition-all" />
            <button type="submit" disabled={loading}
              className="h-12 bg-gradient-to-r from-[#D4A373] to-[#C08F5A] text-white rounded-xl text-sm font-medium hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300 disabled:opacity-60 flex items-center justify-center">
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : '重置密码'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
