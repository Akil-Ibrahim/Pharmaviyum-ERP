import SignIn from "@/features/auth/components/sign-in";
import { Suspense } from "react";

function SignInFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-muted/20 p-6 lg:p-12">
      <div className="mx-auto w-full max-w-[420px] space-y-8">
        <div className="overflow-hidden rounded-2xl border border-gradient-to-r from-violet-500/20 to-fuchsia-500/20 bg-gradient-to-br from-muted/5 to-muted/10 shadow-xl shadow-violet-500/10">
          <img
            src="/Pharmaviyum1.png"
            alt="Pharmaviyum welcome"
            className="w-full object-contain brightness-105 contrast-110 animate-pulse"
          />
        </div>

        <div className="space-y-6">
      </div>
    </div>
  );
}

export default function SignInPage() {
  return (
    <Suspense fallback={<SignInFallback />}>
      <SignIn />
    </Suspense>
  );
}
