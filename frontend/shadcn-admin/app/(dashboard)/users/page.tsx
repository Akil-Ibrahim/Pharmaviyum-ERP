"use client";

import { DataTable } from "@/features/users/components/user-data-table";
import { UserStateCards } from "@/features/users/components/user-state-cards";
import type { User, UserFormValues } from "@/features/users/schema";
import { useEffect, useState } from "react";
import { api } from "@/lib/api-client";

type BackendUser = {
  id: number;
  username: string;
  email?: string | null;
  roles?: string | null;
  is_active: boolean;
  created_at: string;
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const generateAvatar = (name: string) => {
    const names = name.split(" ");
    if (names.length >= 2) {
      return `${names[0][0]}${names[1][0]}`.toUpperCase();
    }
    return name.substring(0, 2).toUpperCase();
  };

  const mapBackendUser = (user: BackendUser): User => ({
    id: user.id,
    name: user.username,
    email: user.email ?? "",
    avatar: generateAvatar(user.username),
    role: user.roles?.split(",")[0] ?? "Subscriber",
    plan: "Basic",
    billing: "Credit Card",
    status: user.is_active ? "Active" : "Inactive",
    joinedDate: new Date(user.created_at).toISOString().split("T")[0],
    lastLogin: new Date(user.created_at).toISOString().split("T")[0],
  });

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const backendUsers = await api.get<BackendUser[]>("/users");
        setUsers(backendUsers.map(mapBackendUser));
      } catch (err) {
        console.error("Failed to load users:", err);
        setError("Unable to load users from backend. Please check your connection.");
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  const handleAddUser = (userData: UserFormValues) => {
    const nextId = users.length > 0 ? Math.max(...users.map((u) => u.id)) + 1 : 1;
    const newUser: User = {
      id: nextId,
      name: userData.name,
      email: userData.email,
      avatar: generateAvatar(userData.name),
      role: userData.role,
      plan: userData.plan,
      billing: userData.billing,
      status: userData.status,
      joinedDate: new Date().toISOString().split("T")[0],
      lastLogin: new Date().toISOString().split("T")[0],
    };
    setUsers((prev) => [newUser, ...prev]);
  };

  const handleDeleteUser = (id: number) => {
    setUsers((prev) => prev.filter((user) => user.id !== id));
  };

  const handleEditUser = (user: User) => {
    console.log("Edit user:", user);
  };

  return (
    <>
      <div className="px-4 lg:px-6 py-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold tracking-tight">Users</h1>
          <p className="text-muted-foreground">Manage users and permissions</p>
          {error ? (
            <p className="text-sm text-red-600">{error}</p>
          ) : loading ? (
            <p className="text-sm text-muted-foreground">Loading users from backend...</p>
          ) : null}
        </div>
      </div>

      <div className="@container/main px-4 lg:px-6 space-y-6">
        <UserStateCards />

        <DataTable
          users={users}
          onDeleteUser={handleDeleteUser}
          onEditUser={handleEditUser}
          onAddUser={handleAddUser}
        />
      </div>
    </>
  );
}
