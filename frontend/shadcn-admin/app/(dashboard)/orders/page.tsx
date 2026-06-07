"use client";

export default function OrdersPage() {
  return (
    <>
      <div className="px-4 lg:px-6 py-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold tracking-tight">Orders</h1>
          <p className="text-muted-foreground">
            Review and manage pharmacy orders, client purchases, and order status.
          </p>
        </div>
      </div>

      <div className="px-4 lg:px-6">
        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <p className="text-sm text-muted-foreground">
            This page is a placeholder for the Orders entity. Connect it to
            <code className="rounded bg-muted px-1 py-0.5">/api/v1/orders</code>
            endpoints and render order history here.
          </p>
        </div>
      </div>
    </>
  );
}
