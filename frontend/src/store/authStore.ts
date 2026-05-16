import { create } from "zustand";
import type { User, UserRole } from "@/types/auth";

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  role: UserRole | null;
  setUser: (user: User) => void;
  clearAuth: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: true,
  role: null,

  setUser: (user) =>
    set({ user, isAuthenticated: true, isLoading: false, role: user.role }),

  clearAuth: () =>
    set({ user: null, isAuthenticated: false, isLoading: false, role: null }),

  setLoading: (loading) => set({ isLoading: loading }),
}));
