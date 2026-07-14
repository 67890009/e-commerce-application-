// src/components/auth/LoginForm.js
"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useDispatch, useSelector } from "react-redux";
import GoogleButton from "@/components/auth/GoogleButton";
import { loginSchema } from "@/lib/validators/authSchemas";
import { loginUser, selectAuthStatus, selectAuthError, clearAuthError } from "@/features/auth/authSlice";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import Link from "next/link";

// Central place for the redirect rule — if this logic changes, it changes
// in exactly one spot, not scattered across every place that logs a user in
// (e.g. this will also be reused by OTP login and Google OAuth callback).
export function getPostLoginRedirect(user) {
  if (!user) return "/login";
  if (user.role === "admin") return "/admin/dashboard";
  if (user.role === "seller") {
    return user.seller_approved ? "/seller/dashboard" : "/seller/pending";
  }
  return "/"; // customer
}

export default function LoginForm() {
  const router = useRouter();
  const dispatch = useDispatch();
  const status = useSelector(selectAuthStatus);
  const serverError = useSelector(selectAuthError);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  const onSubmit = async (data) => {
    dispatch(clearAuthError());
    const result = await dispatch(loginUser(data));

    if (loginUser.fulfilled.match(result)) {
      const redirectPath = getPostLoginRedirect(result.payload.user);
      router.push(redirectPath);
    }
    // rejected: serverError populated in Redux, rendered below
  };

  const isSubmitting = status === "loading";
  const isUnverifiedError = serverError?.toLowerCase().includes("verify");

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 w-full max-w-md">
      {serverError && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {serverError}
          {isUnverifiedError && (
            <Link href="/verify-email" className="block mt-1 font-medium underline underline-offset-2">
              Resend verification email
            </Link>
          )}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" {...register("email")} placeholder="you@example.com" />
        {errors.email && <p className="text-sm text-red-600">{errors.email.message}</p>}
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <Label htmlFor="password">Password</Label>
          <Link href="/forgot-password" className="text-xs text-muted-foreground underline underline-offset-2">
            Forgot password?
          </Link>
        </div>
        <Input id="password" type="password" {...register("password")} />
        {errors.password && <p className="text-sm text-red-600">{errors.password.message}</p>}
      </div>

      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "Logging in..." : "Log in"}
      </Button>
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-muted" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-background px-2 text-muted-foreground">
            Or continue with
          </span>
        </div>
      </div>
      <GoogleButton/>

      <div className="text-sm text-center text-muted-foreground">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="font-medium text-foreground underline underline-offset-4">
          Sign up
        </Link>
      </div>
    </form>
  );
}