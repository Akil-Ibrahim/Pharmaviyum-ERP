/**
 * TypeScript interfaces mirroring FastAPI Pydantic schemas.
 * Generated from: src/pharmaviyum/schemas/*.py and models/*.py
 */

// Auth & Users (src/pharmaviyum/models/user.py)
export interface User {
  id: string;
  email: string;
  role: "admin" | "pharmacist" | "developer";
  is_active: boolean;
  created_at: string;
}

// Clients (src/pharmaviyum/models/client.py)
export interface Client {
  id: string;
  name: string;
  inn: string;
  contact_email: string;
  status: "active" | "blocked";
  created_at: string;
}

// Products (src/pharmaviyum/models/product.py)
export interface Product {
  id: string;
  sku: string;
  name: string;
  price: number;
  stock: number;
  category: string;
}

// Orders (src/pharmaviyum/models/order.py)
export interface Order {
  id: string;
  client_id: string;
  status: "pending" | "processing" | "shipped" | "delivered" | "cancelled";
  total: number;
  items: { product_id: string; qty: number; price: number }[];
  created_at: string;
  updated_at: string;
}
// Audit Logs (src/pharmaviyum/models/audit_log.py)
export interface AuditLog {
  id: string;
  user_id: string;
  action: "create" | "update" | "delete" | "login";
  entity: "user" | "client" | "order" | "product";
  entity_id: string;
  ip_address: string;
  timestamp: string;
}

// RAG Assistant (src/pharmaviyum/api/rag.py)
export type ChatRole = "user" | "assistant" | "system";
export interface RAGMessage {
  id: string;
  role: ChatRole;
  content: string;
  sources?: string[];
  timestamp: string;
}

export interface RAGSession {
  id: string;
  user_id: string;
  created_at: string;
  messages: RAGMessage[];
}

// Pagination wrapper used by FastAPI endpoints
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
