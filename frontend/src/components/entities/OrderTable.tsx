/**
 * Orders data table mapped from FastAPI /api/v1/orders/
 * Demonstrates column definitions, status badges, and row actions.
 * Replicate this pattern for Clients, Products, Users, AuditLogs.
 */

"use client";
import { ColumnDef } from "@tanstack/react-table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { MoreHorizontal, Pencil, Trash2 } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { DataTable } from "@/components/ui/data-table";
import { Order } from "@/lib/types";

const statusVariant: Record<Order["status"], "default" | "secondary" | "destructive" | "outline"> = {
  pending: "secondary",
  processing: "outline",
  shipped: "default",
  delivered: "default",
  cancelled: "destructive",
};

export const columns: ColumnDef<Order>[] = [
  { accessorKey: "id", header: "Order ID", cell: ({ row }) => row.getValue("id").toString().slice(0, 8) },
  { accessorKey: "client_id", header: "Client" },
  { accessorKey: "total", header: "Total", cell: ({ row }) => `₽${Number(row.getValue("total")).toLocaleString()}` },
  {
    accessorKey: "status",
    header: "Status",
    cell: ({ row }) => {
      const status = row.getValue("status") as Order["status"];
      return <Badge variant={statusVariant[status]}>{status}</Badge>;    },
  },
  { accessorKey: "created_at", header: "Created", cell: ({ row }) => new Date(row.getValue("created_at")).toLocaleDateString() },
  {
    id: "actions",
    cell: ({ row }) => (
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon"><MoreHorizontal className="h-4 w-4" /></Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          <DropdownMenuItem onClick={() => console.log("Edit", row.original.id)}><Pencil className="mr-2 h-4 w-4" /> Edit</DropdownMenuItem>
          <DropdownMenuItem className="text-red-600" onClick={() => console.log("Delete", row.original.id)}><Trash2 className="mr-2 h-4 w-4" /> Delete</DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    ),
  },
];

export function OrderTable({ data }: { data: Order[] }) {
  return <DataTable columns={columns} data={data} searchKey="client_id" />;
}
