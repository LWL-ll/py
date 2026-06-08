import { createContext, useContext, useState, useEffect, useCallback, type ReactNode } from 'react';

interface User {
  username: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/lauth/check-login/')
      .then((r) => r.json())
      .then((data) => {
        if (data.is_authenticated) setUser({ username: data.username });
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const logout = useCallback(async () => {
    await fetch('/lauth/user-logout/', { method: 'POST' }).catch(() => {});
    setUser(null);
    window.location.href = '/lauth/login/';
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
