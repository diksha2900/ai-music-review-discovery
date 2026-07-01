"use client";

import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { authMe } from "@/lib/api";
import { captureSessionFromUrl, clearSessionId } from "@/lib/session";

type User = { logged_in: boolean; display_name?: string };

type AuthContextValue = {
  user: User | null;
  loading: boolean;
  refresh: () => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<AuthContextValue>({
  user: null,
  loading: true,
  refresh: async () => {},
  logout: () => {},
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const refresh = useCallback(async () => {
    const me = await authMe();
    setUser(me);
    setLoading(false);
  }, []);

  useEffect(() => {
    captureSessionFromUrl();
    refresh();
  }, [refresh, pathname, searchParams]);

  function logout() {
    clearSessionId();
    setUser({ logged_in: false });
  }

  return (
    <AuthContext.Provider value={{ user, loading, refresh, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
