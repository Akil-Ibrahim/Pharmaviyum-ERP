"use client";

export default function ClientsPage() {
  return (
    <>
      <div className="px-4 lg:px-6 py-4">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-bold tracking-tight">Clients</h1>
          <p className="text-muted-foreground">
            Manage customers, view client profiles, and trigger AI recommendations.
          </p>
        </div>
      </div>

      <div className="px-4 lg:px-6">
        <div className="rounded-lg border bg-card p-6 shadow-sm">
          <p className="text-sm text-muted-foreground">
            This page is a placeholder for the Clients entity. Connect it to
            <code className="rounded bg-muted px-1 py-0.5">/api/v1/clients</code>
            endpoints and render the client list here.
          </p>
        </div>
      </div>
    </>
  );
}
