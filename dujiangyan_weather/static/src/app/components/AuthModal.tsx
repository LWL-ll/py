import { useState } from 'react';
import { Loader2, X } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

type Tab = 'login' | 'register' | 'forgot';

interface Props {
  onClose: () => void;
}

export default function AuthModal({ onClose }: Props) {
  const { login, register, sendCode, sendResetCode, resetPassword } = useAuth();
  const [tab, setTab] = useState<Tab>('login');
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState('');
  const [msgType, setMsgType] = useState<'info' | 'error' | 'success'>('info');

  // 表单字段
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);

  const showMsg = (message: string, type: 'info' | 'error' | 'success' = 'info') => {
    setMsg(message);
    setMsgType(type);
  };

  /** 发送验证码 */
  const handleSendCode = async () => {
    if (!email) { showMsg('请输入邮箱', 'error'); return; }
    setLoading(true);
    const r = await sendCode(email);
    showMsg(r.message, r.ok ? 'success' : 'error');
    if (r.ok) setCodeSent(true);
    setLoading(false);
  };

  /** 发送重置密码验证码 */
  const handleSendReset = async () => {
    if (!email) { showMsg('请输入邮箱', 'error'); return; }
    setLoading(true);
    const r = await sendResetCode(email);
    showMsg(r.message, r.ok ? 'success' : 'error');
    if (r.ok) setCodeSent(true);
    setLoading(false);
  };

  /** 登录 */
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { showMsg('请填写邮箱和密码', 'error'); return; }
    setLoading(true);
    const r = await login(email, password);
    showMsg(r.message, r.ok ? 'success' : 'error');
    if (r.ok) setTimeout(onClose, 800);
    setLoading(false);
  };

  /** 注册 */
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username || !email || !password || !code) {
      showMsg('请填写所有字段', 'error'); return;
    }
    if (username.length < 3) { showMsg('用户名至少3个字符', 'error'); return; }
    if (password.length < 6) { showMsg('密码至少6个字符', 'error'); return; }

    setLoading(true);
    const r = await register(username, email, password, code);
    showMsg(r.message, r.ok ? 'success' : 'error');
    if (r.ok) setTimeout(onClose, 800);
    setLoading(false);
  };

  /** 重置密码 */
  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !code || !password) {
      showMsg('请填写所有字段', 'error'); return;
    }
    if (password.length < 6) { showMsg('新密码至少6个字符', 'error'); return; }
    setLoading(true);
    const r = await resetPassword(email, code, password);
    showMsg(r.message, r.ok ? 'success' : 'error');
    if (r.ok) setTimeout(() => { setTab('login'); setMsg(''); }, 1500);
    setLoading(false);
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: 'login', label: '登录' },
    { key: 'register', label: '注册' },
    { key: 'forgot', label: '忘记密码' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30" onClick={onClose}>
      <div className="bg-white rounded-2xl shadow-2xl w-[400px] max-w-[95vw] p-6" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between mb-5">
          <div className="flex gap-1">
            {tabs.map((t) => (
              <button
                key={t.key}
                onClick={() => { setTab(t.key); setMsg(''); setCodeSent(false); }}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                  tab === t.key ? 'bg-[#4A6FA5] text-white' : 'text-[#8E8E93] hover:bg-[#FAFAF8]'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
          <button onClick={onClose} className="p-1 rounded-lg hover:bg-[#FAFAF8]">
            <X className="w-5 h-5 text-[#8E8E93]" />
          </button>
        </div>

        {/* Message */}
        {msg && (
          <div className={`mb-4 px-3 py-2 rounded-lg text-xs ${
            msgType === 'error' ? 'bg-[#E07A5F15] text-[#E07A5F]' :
            msgType === 'success' ? 'bg-[#81B29A15] text-[#81B29A]' :
            'bg-[#4A6FA515] text-[#4A6FA5]'
          }`}>
            {msg}
          </div>
        )}

        {/* Login Form */}
        {tab === 'login' && (
          <form onSubmit={handleLogin} className="flex flex-col gap-4">
            <input type="email" placeholder="邮箱地址" value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="h-11 px-4 border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]" />
            <input type="password" placeholder="密码" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-11 px-4 border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]" />
            <button type="submit" disabled={loading}
              className="h-11 bg-[#4A6FA5] text-white rounded-xl text-sm font-medium hover:bg-[#3D5A8A] disabled:opacity-60 flex items-center justify-center">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '登录'}
            </button>
          </form>
        )}

        {/* Register Form */}
        {tab === 'register' && (
          <form onSubmit={handleRegister} className="flex flex-col gap-3">
            <input type="text" placeholder="用户名（至少3个字符）" value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="h-11 px-4 border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]" />
            <div className="flex gap-2">
              <input type="email" placeholder="邮箱地址" value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 h-11 px-4 border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]" />
              <button type="button" onClick={handleSendCode} disabled={loading}
                className="h-11 px-3 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-xs text-[#4A6FA5] hover:bg-[#F0F0EB] whitespace-nowrap disabled:opacity-60">
                {codeSent ? '已发送' : '发送验证码'}
              </button>
            </div>
            <input type="text" placeholder="验证码（6位数字）" value={code} maxLength={6}
              onChange={(e) => setCode(e.target.value)}
              className="h-11 px-4 border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]" />
            <input type="password" placeholder="密码（至少6个字符）" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-11 px-4 border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]" />
            <button type="submit" disabled={loading}
              className="h-11 bg-[#81B29A] text-white rounded-xl text-sm font-medium hover:bg-[#6A9A7F] disabled:opacity-60 flex items-center justify-center">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '注册'}
            </button>
          </form>
        )}

        {/* Forgot Password Form */}
        {tab === 'forgot' && (
          <form onSubmit={handleReset} className="flex flex-col gap-3">
            <div className="flex gap-2">
              <input type="email" placeholder="注册邮箱" value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="flex-1 h-11 px-4 border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]" />
              <button type="button" onClick={handleSendReset} disabled={loading}
                className="h-11 px-3 bg-[#FAFAF8] border border-[#E8E8E6] rounded-xl text-xs text-[#4A6FA5] hover:bg-[#F0F0EB] whitespace-nowrap disabled:opacity-60">
                {codeSent ? '已发送' : '发送验证码'}
              </button>
            </div>
            <input type="text" placeholder="验证码（6位数字）" value={code} maxLength={6}
              onChange={(e) => setCode(e.target.value)}
              className="h-11 px-4 border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]" />
            <input type="password" placeholder="新密码（至少6个字符）" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="h-11 px-4 border border-[#E8E8E6] rounded-xl text-sm outline-none focus:border-[#4A6FA5]" />
            <button type="submit" disabled={loading}
              className="h-11 bg-[#D4A373] text-white rounded-xl text-sm font-medium hover:bg-[#C08F5A] disabled:opacity-60 flex items-center justify-center">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : '重置密码'}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
