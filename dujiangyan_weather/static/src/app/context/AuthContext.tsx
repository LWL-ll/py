import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';
import { apiFetch } from '../utils/api';

interface User {
  username: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<{ ok: boolean; message: string }>;
  register: (username: string, email: string, password: string) => Promise<{ ok: boolean; message: string }>;
  logout: () => Promise<void>;
  sendCode: (email: string) => Promise<{ ok: boolean; message: string }>;
  verifyCode: (email: string, code: string) => Promise<{ ok: boolean; message: string }>;
  sendResetCode: (email: string) => Promise<{ ok: boolean; message: string }>;
  resetPassword: (email: string, code: string, newPassword: string) => Promise<{ ok: boolean; message: string }>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  // 检查登录状态
  useEffect(() => {
    fetch('/lauth/check-login/')
      .then((r) => r.json())
      .then((data) => {
        if (data.is_authenticated) {
          setUser({ username: data.username });
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  /** 登录 */
  const login = useCallback(async (email: string, password: string) => {
    try {
      const res = await apiFetch('/lauth/user-login/', {
        method: 'POST',
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (data.success) {
        setUser({ username: data.username });
        return { ok: true, message: data.message };
      }
      return { ok: false, message: data.message };
    } catch {
      return { ok: false, message: '网络错误' };
    }
  }, []);

  /** 注册（完整流程：用户名+邮箱+密码+验证码） */
  const register = useCallback(async (username: string, email: string, password: string, code: string) => {
    try {
      const res = await apiFetch('/lauth/register-user/', {
        method: 'POST',
        body: JSON.stringify({ username, email, password, verification_code: code }),
      });
      const data = await res.json();
      if (data.success && data.username) {
        setUser({ username: data.username });
      }
      return { ok: data.success, message: data.message };
    } catch {
      return { ok: false, message: '网络错误' };
    }
  }, []);

  /** 退出 */
  const logout = useCallback(async () => {
    await apiFetch('/lauth/user-logout/', { method: 'POST' }).catch(() => {});
    setUser(null);
  }, []);

  /** 发送验证码 */
  const sendCode = useCallback(async (email: string) => {
    try {
      const res = await apiFetch('/lauth/send-code/', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      return { ok: data.success, message: data.message };
    } catch {
      return { ok: false, message: '网络错误' };
    }
  }, []);

  /** 验证验证码 */
  const verifyCode = useCallback(async (email: string, code: string) => {
    try {
      const res = await apiFetch('/lauth/verify-code/', {
        method: 'POST',
        body: JSON.stringify({ email, code }),
      });
      const data = await res.json();
      return { ok: data.success, message: data.message };
    } catch {
      return { ok: false, message: '网络错误' };
    }
  }, []);

  /** 发送重置密码验证码 */
  const sendResetCode = useCallback(async (email: string) => {
    try {
      const res = await apiFetch('/lauth/send-reset-code/', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      return { ok: data.success, message: data.message };
    } catch {
      return { ok: false, message: '网络错误' };
    }
  }, []);

  /** 重置密码 */
  const resetPassword = useCallback(async (email: string, code: string, newPassword: string) => {
    try {
      const res = await apiFetch('/lauth/reset-password/', {
        method: 'POST',
        body: JSON.stringify({ email, code, new_password: newPassword }),
      });
      const data = await res.json();
      return { ok: data.success, message: data.message };
    } catch {
      return { ok: false, message: '网络错误' };
    }
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, sendCode, verifyCode, sendResetCode, resetPassword }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
