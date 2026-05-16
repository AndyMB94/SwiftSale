import api from "./api";
import type { AuthResponse, LoginCredentials, User } from "@/types/auth";

export const login = (credentials: LoginCredentials) =>
  api.post<AuthResponse>("/api/v1/auth/login", credentials);

export const logout = () => api.post("/api/v1/auth/logout");

export const getMe = () => api.get<User>("/api/v1/auth/me");

export const refreshToken = () => api.post("/api/v1/auth/refresh");
