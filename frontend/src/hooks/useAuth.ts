"use client";

import { useEffect } from "react";
import { useAuthStore } from "@/store/authStore";
import { getMe } from "@/services/auth";

export function useAuthInit() {
  const setUser = useAuthStore((s) => s.setUser);
  const clearAuth = useAuthStore((s) => s.clearAuth);

  useEffect(() => {
    getMe()
      .then(({ data }) => setUser(data))
      .catch(() => clearAuth());
  }, [setUser, clearAuth]);
}
