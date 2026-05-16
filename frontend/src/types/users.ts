export type UserRole = "admin" | "supervisor" | "cashier";

export interface AppUser {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface UserListResponse {
  count: number;
  results: AppUser[];
}

export interface CreateUserInput {
  email: string;
  full_name: string;
  role: UserRole;
  password: string;
}

export interface UpdateUserInput {
  full_name?: string;
  role?: UserRole;
  is_active?: boolean;
}
