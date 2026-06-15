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
      await login(data.login, data.password);
      toast.success("Signed in successfully!");
      const callbackUrl = searchParams.get("callbackUrl") || "/dashboard2";
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
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-muted/20 p-6 lg:p-12">
      <div className="mx-auto w-full max-w-[420px] space-y-8">
        <div className="overflow-hidden rounded-2xl border border-gradient-to-r from-violet-500/20 to-fuchsia-500/20 bg-gradient-to-br from-muted/5 to-muted/10 shadow-xl shadow-violet-500/10 hover:shadow-2xl hover:shadow-violet-500/20 transition-all duration-300">
          <img
            src="/Pharmaviyum1.png"
            alt="Pharmaviyum welcome"
            className="h-64 w-full object-cover brightness-105 contrast-110 hover:brightness-110 transition-all duration-300"
          />
        </div>

        <div className="text-center space-y-2">
          <h1 className="text-4xl font-bold tracking-tight bg-gradient-to-r from-violet-600 to-fuchsia-600 bg-clip-text text-transparent">Admin Login</h1>
          <p className="text-sm text-muted-foreground">Secure access to your dashboard</p>
        </div>

        <div className="space-y-6">
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
              <FormField
                control={form.control}
                name="login"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel className="text-sm font-semibold">Login</FormLabel>
                    <FormControl>
                      <Input
                        type="text"
                        placeholder="Enter your username"
                        disabled={isLoading}
                        className="h-11 px-4 bg-gradient-to-r from-muted/40 to-muted/20 border border-muted-foreground/30 rounded-lg text-sm placeholder:text-muted-foreground/60 transition-all duration-200 focus:border-violet-500/50 focus:bg-gradient-to-r focus:from-muted/60 focus:to-muted/40 focus:ring-2 focus:ring-violet-500/20 focus:outline-none hover:border-muted-foreground/40"
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
                      <FormLabel className="text-sm font-semibold">Password</FormLabel>
                      <Link
                        href="/forgot-password"
                        className="text-xs text-muted-foreground hover:text-violet-600 transition-colors font-medium"
                      >
                        Forgot password?
                      </Link>
                    </div>
                    <FormControl>
                      <div className="relative">
                        <Input
                          type={showPassword ? "text" : "password"}
                          placeholder="Enter your password"
                          disabled={isLoading}
                          className="h-11 px-4 bg-gradient-to-r from-muted/40 to-muted/20 border border-muted-foreground/30 rounded-lg text-sm placeholder:text-muted-foreground/60 transition-all duration-200 focus:border-violet-500/50 focus:bg-gradient-to-r focus:from-muted/60 focus:to-muted/40 focus:ring-2 focus:ring-violet-500/20 focus:outline-none hover:border-muted-foreground/40 pr-11"
                          onBeforeInput={blockDisallowedPasswordChars}
                          {...field}
                        />
                        <p className="mt-2 text-xs text-muted-foreground">
                          Demo: <span className="font-medium text-foreground/70">Admin123!@#</span>
                        </p>
                        <button
                          type="button"
                          onClick={() => setShowPassword(!showPassword)}
                          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-violet-600 transition-colors p-1"
                          tabIndex={-1}
                        >
                          {showPassword ? <EyeOff className="size-5" /> : <Eye className="size-5" />}
                        </button>
                      </div>
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <Button
                className="h-11 w-full bg-gradient-to-r from-violet-600 to-fuchsia-600 font-semibold text-white text-sm transition-all duration-200 hover:from-violet-700 hover:to-fuchsia-700 hover:shadow-lg hover:shadow-violet-500/30 active:scale-95 disabled:opacity-50 rounded-lg mt-1"
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
  );
}
