"use client";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { useAuth } from "@/contexts/auth-context";
import { cn } from "@/lib/utils";
import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";
import { blockDisallowedPasswordChars } from "../schemas/password-validation";
import { SignInSchema, signInSchema } from "../schemas/sign-in-schema";

export default function SignIn() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { login } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const form = useForm<SignInSchema>({
    resolver: zodResolver(signInSchema),
    defaultValues: {
      login: "",
      password: "",
    },
  });

  const onSubmit = async (data: SignInSchema) => {
    try {
      setIsLoading(true);
      // Use login as username for auth
      await login(data.login, data.password);
      toast.success("Signed in successfully!");
      const callbackUrl = searchParams.get("callbackUrl") || "/dashboard";
      router.push(callbackUrl);
      router.refresh();
    } catch (error) {
      console.error("Sign in error:", error);
      toast.error(
        error instanceof Error
          ? error.message
          : "Failed to sign in. Please check your credentials.",
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="relative grid min-h-screen w-full lg:grid-cols-2">
      {/* Left Column - Animated Background */}
      <div className="relative hidden overflow-hidden bg-zinc-950 lg:block">
        <div className="absolute inset-0 bg-linear-to-br from-violet-600/20 via-transparent to-cyan-600/20" />
        <div className="absolute inset-0 bg-linear-to-tr from-fuchsia-600/10 via-transparent to-amber-600/10 animate-pulse" />
        <div
          className="absolute inset-0 opacity-20"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,.05) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,.05) 1px, transparent 1px)`,
            backgroundSize: "50px 50px",
          }}
        />

        <div className="absolute top-1/4 left-1/4 h-72 w-72 rounded-full bg-linear-to-r from-violet-500 to-fuchsia-500 opacity-20 blur-3xl animate-[pulse_4s_ease-in-out_infinite]" />
        <div className="absolute bottom-1/4 right-1/4 h-96 w-96 rounded-full bg-linear-to-r from-cyan-500 to-blue-500 opacity-20 blur-3xl animate-[pulse_5s_ease-in-out_infinite_1s]" />
        <div className="absolute top-1/2 right-1/3 h-64 w-64 rounded-full bg-linear-to-r from-amber-500 to-orange-500 opacity-10 blur-3xl animate-[pulse_6s_ease-in-out_infinite_2s]" />

        <div className="absolute top-20 right-20 h-20 w-20 rotate-45 rounded-xl border border-white/10 bg-white/5 backdrop-blur-sm animate-[bounce_6s_ease-in-out_infinite]" />
        <div className="absolute bottom-32 left-20 h-16 w-16 rounded-full border border-white/10 bg-white/5 backdrop-blur-sm animate-[bounce_5s_ease-in-out_infinite_1s]" />
        <div className="absolute top-1/2 left-1/4 h-12 w-12 rotate-12 rounded-lg border border-white/10 bg-white/5 backdrop-blur-sm animate-[bounce_7s_ease-in-out_infinite_0.5s]" />

        <div className="relative z-10 flex h-full flex-col justify-between p-12">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-linear-to-br from-violet-500 to-fuchsia-500 text-lg font-bold text-white shadow-lg shadow-violet-500/25 transition-transform group-hover:scale-105">
              SA
            </div>
            <div className="flex flex-col">
              <span className="text-xl font-semibold text-white">
                Shadcn Admin
              </span>
              <span className="text-sm text-zinc-400">Admin Dashboard</span>
            </div>
          </Link>

          <div className="flex flex-col items-center justify-center space-y-6">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-8 backdrop-blur-xl">
              <div className="flex items-center gap-4">
                <div className="flex -space-x-3">
                  {[...Array(4)].map((_, i) => (
                    <div
                      key={i}
                      className={cn(
                        "h-10 w-10 rounded-full border-2 border-zinc-950 bg-linear-to-br",
                        i === 0 && "from-violet-400 to-violet-600",
                        i === 1 && "from-cyan-400 to-cyan-600",
                        i === 2 && "from-fuchsia-400 to-fuchsia-600",
                        i === 3 && "from-amber-400 to-amber-600",
                      )}
                    />
                  ))}
                </div>
                <div className="text-white">
                  <p className="font-medium">Join 10,000+ users</p>
                  <p className="text-sm text-zinc-400">
                    Building amazing dashboards
                  </p>
                </div>
              </div>
            </div>
          </div>

          <div className="max-w-md space-y-4">
            <blockquote className="text-lg italic text-zinc-300">
              &ldquo;This dashboard has transformed how we manage our business.
              The interface is beautiful and intuitive.&rdquo;
            </blockquote>
          </div>
        </div>
      </div>

      {/* Right Column - Sign In Form */}
      <div className="flex items-center justify-center bg-background p-6 lg:p-12">
        <div className="mx-auto w-full max-w-[400px] space-y-8">
          <div className="flex items-center justify-center gap-3 lg:hidden">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-linear-to-br from-violet-500 to-fuchsia-500 text-sm font-bold text-white">
              SA
            </div>
            <span className="text-lg font-semibold">Shadcn Admin</span>
          </div>

          <div className="space-y-2 text-center lg:text-left">
            <h1 className="text-3xl font-bold tracking-tight">Welcome back</h1>
            <p className="text-muted-foreground">
              Sign in to your account to continue
            </p>
          </div>

          <div className="space-y-6">
            <div className="rounded-2xl border border-muted p-4 bg-muted/5 text-sm text-muted-foreground">
              Use admin credentials:
              <div className="mt-2 font-medium text-foreground">
                admin / admin
              </div>
            </div>

            <Form {...form}>
              <form
                onSubmit={form.handleSubmit(onSubmit)}
                className="space-y-4"
              >
                <FormField
                  control={form.control}
                  name="login"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Login</FormLabel>
                      <FormControl>
                        <Input
                          type="text"
                          placeholder="admin"
                          disabled={isLoading}
                          className="h-12 bg-muted/30 border-muted-foreground/20 transition-colors focus:bg-background"
                          {...field}
                        />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="password"
                  render={({ field }) => (
                    <FormItem>
                      <div className="flex items-center justify-between">
                        <FormLabel>Password</FormLabel>
                        <Link
                          href="/forgot-password"
                          className="text-sm text-muted-foreground hover:text-primary transition-colors"
                        >
                          Forgot password?
                        </Link>
                      </div>
                      <FormControl>
                        <div className="relative">
                          <Input
                            type={showPassword ? "text" : "password"}
                            placeholder="Admin123!@#"
                            disabled={isLoading}
                            className="h-12 bg-muted/30 border-muted-foreground/20 transition-colors focus:bg-background pr-12"
                            onBeforeInput={blockDisallowedPasswordChars}
                            {...field}
                          />
                          <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
                            tabIndex={-1}
                          >
                            {showPassword ? (
                              <EyeOff className="size-5" />
                            ) : (
                              <Eye className="size-5" />
                            )}
                          </button>
                        </div>
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <Button
                  className="h-12 w-full bg-linear-to-r from-violet-600 to-fuchsia-600 font-medium text-white transition-all hover:from-violet-700 hover:to-fuchsia-700 hover:shadow-lg hover:shadow-violet-500/25"
                  type="submit"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <span className="flex items-center gap-2">
                      <svg className="size-4 animate-spin" viewBox="0 0 24 24">
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                          fill="none"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        />
                      </svg>
                      Signing in...
                    </span>
                  ) : (
                    "Sign in"
                  )}
                </Button>
              </form>
            </Form>
          </div>
        </div>
      </div>
    </div>
  );
}
