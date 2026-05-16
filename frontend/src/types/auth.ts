export type UserRole = "admin" | "supervisor" | "cashier";

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthResponse {
  user: User;
  message: string;
}
