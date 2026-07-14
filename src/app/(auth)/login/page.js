// src/app/(auth)/login/page.js

import LoginForm from "@/components/auth/LoginForm";

export const metadata = {
  title: "Log in",
};

export default function LoginPage() {
  return (
    <div className="w-full max-w-md space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Welcome back</h1>
        <p className="text-sm text-muted-foreground">
          Log in to your account to continue.
        </p>
      </div>
      <LoginForm />
    </div>
  );
}