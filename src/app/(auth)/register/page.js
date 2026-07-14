// src/app/(auth)/register/page.js

import RegisterForm from "@/components/auth/RegisterForm";

export const metadata = {
  title: "Create an account",
};

export default function RegisterPage() {
  return (
    <div className="w-full max-w-md space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Create an account</h1>
        <p className="text-sm text-muted-foreground">
          Enter your details below to get started.
        </p>
      </div>
      <RegisterForm />
      <p className="text-sm text-center text-muted-foreground">
        Already have an account?{" "}
        <a href="/login" className="font-medium text-foreground underline underline-offset-4">
          Log in
        </a>
      </p>
    </div>
  );
}