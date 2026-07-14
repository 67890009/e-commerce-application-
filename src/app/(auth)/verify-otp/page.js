// src/app/(auth)/verify-otp/page.js

import OtpForm from "@/components/auth/OtpForm";

export const metadata = {
  title: "Log in with phone",
};

export default function VerifyOtpPage() {
  return (
    <div className="w-full max-w-md space-y-8">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">Log in with phone</h1>
        <p className="text-sm text-muted-foreground">
          We&apos;ll text you a one-time code — no password needed.
        </p>
      </div>
      <OtpForm />
    </div>
  );
}