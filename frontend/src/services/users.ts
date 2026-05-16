import api from "./api";
import type {
  AppUser,
  CreateUserInput,
  UpdateUserInput,
  UserListResponse,
} from "@/types/users";

export const listUsers = () =>
  api.get<UserListResponse>("/api/v1/users/");

export const createUser = (data: CreateUserInput) =>
  api.post<AppUser>("/api/v1/users/", data);

export const updateUser = (id: string, data: UpdateUserInput) =>
  api.put<AppUser>(`/api/v1/users/${id}`, data);
