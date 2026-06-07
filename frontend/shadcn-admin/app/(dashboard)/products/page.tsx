"use client";

export default function ProductsPage() {
  return (
    <>
      <div className="px-4 lg:px-6 py-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold tracking-tight">Products</h1>
          <p className="text-muted-foreground">
            Manage pharmacy products, SKUs, stock levels, and pricing.
          </p>
        </div>
      </div>

      <div className="px-4 lg:px-6">
        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <p className="text-sm text-muted-foreground">
            This page is a placeholder for the Products entity. Connect it to
            <code className="rounded bg-muted px-1 py-0.5">/api/v1/products</code>
            endpoints and render product management tools here.
          </p>
        </div>
      </div>
    </>
  );
}
