import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted flex flex-col items-center justify-center p-4">
      <div className="text-center space-y-6 max-w-2xl">
        <div className="space-y-2">
          <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
            Pharmaviyum CRM
          </h1>
          <p className="text-xl text-muted-foreground">
            A modern admin dashboard for pharmacy management integrated with ERP systems
          </p>
        </div>

        <div className="flex gap-4 justify-center pt-4">
          <Link
            href="#"
            className="px-8 py-3 rounded-lg bg-primary text-primary-foreground font-medium hover:opacity-90 transition-opacity"
          >
            Get Started
          </Link>
          <Link
            href="#"
            className="px-8 py-3 rounded-lg border border-border text-foreground font-medium hover:bg-muted transition-colors"
          >
            Learn More
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-12">
          {[
            { title: "Dashboard", desc: "Real-time analytics and insights" },
            { title: "Inventory", desc: "Manage pharmacy stock efficiently" },
            { title: "Orders", desc: "Track and process customer orders" },
          ].map((feature) => (
            <div
              key={feature.title}
              className="p-6 rounded-lg border border-border bg-card hover:bg-muted/50 transition-colors"
            >
              <h3 className="font-semibold text-lg mb-2">{feature.title}</h3>
              <p className="text-sm text-muted-foreground">{feature.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
