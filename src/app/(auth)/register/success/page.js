// src/app/register/success/page.js
"use client";

import { useSearchParams } from "next/navigation";
import { Suspense } from "react";
import { Button } from "@/components/ui/button";
import Link from "next/link";

function SuccessContent() {
  const searchParams = useSearchParams();
  const type = searchParams.get("type"); // "customer" | "seller"

  const isSeller = type === "seller";

  return (
    <div className="max-w-md w-full text-center space-y-6">
      <div className="mx-auto w-14 h-14 rounded-full bg-green-100 flex items-center justify-center">
        <svg
          className="w-7 h-7 text-green-600"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M5 13l4 4L19 7"
          />
        </svg>
      </div>

      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          {isSeller ? "Application submitted" : "Check your email"}
        </h1>

        <p className="text-sm text-muted-foreground">
          {isSeller
            ? "Your seller account has been created. Our team will review your application and notify you by email once it's approved — usually within 1-2 business days."
            : "We've sent a verification link to your email. Click it to activate your account, then come back to log in."}
        </p>
      </div>

      {isSeller && (
        <p className="text-xs text-muted-foreground bg-zinc-50 border rounded-md px-4 py-3">
          You can log in now to check your application status anytime.
        </p>
      )}

      <Button asChild className="w-full">
        <Link href="/login">Go to login</Link>
      </Button>
    </div>
  );
}

// useSearchParams requires a Suspense boundary in App Router
export default function RegisterSuccessPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <Suspense fallback={null}>
        <SuccessContent />
      </Suspense>
    </div>
  );
}