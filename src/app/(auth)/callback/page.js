// src/app/auth/callback/page.js
"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useDispatch } from "react-redux";
import { Suspense } from "react";

import { googleExchange } from "@/features/auth/authSlice";
import { getPostLoginRedirect } from "@/components/auth/LoginForm";

function CallbackContent() {
  const router = useRouter();
  const dispatch = useDispatch();
  const searchParams = useSearchParams();
  const [error, setError] = useState(null);
  const ranOnce = useRef(false);

  useEffect(() => {
    // Guard against double-exchange (StrictMode double-invoke, or user
    // hitting back/forward). Exchanging the same code twice would fail
    // anyway since backend codes are one-time-use, but fail loudly once,
    // not twice with a confusing race.
    if (ranOnce.current) return;
    ranOnce.current = true;

    const code = searchParams.get("code");

    if (!code) {
      setError("Missing authorization code. Please try signing in again.");
      return;
    }

    dispatch(googleExchange({ code })).then((result) => {
      if (googleExchange.fulfilled.match(result)) {
        const redirectPath = getPostLoginRedirect(result.payload.user);
        router.replace(redirectPath);
      } else {
        setError(result.payload || "Google sign-in failed. Please try again.");
      }
    });
  }, [searchParams, dispatch, router]);

  if (error) {
    return (
      <div className="max-w-md w-full text-center space-y-4">
        <p className="text-sm text-red-600">{error}</p>
        <a href="/login" className="text-sm underline underline-offset-4">
          Back to login
        </a>
      </div>
    );
  }

  return (
    <div className="max-w-md w-full text-center space-y-4">
      <p className="text-sm text-muted-foreground">Signing you in...</p>
    </div>
  );
}

export default function GoogleCallbackPage() {
  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <Suspense fallback={null}>
        <CallbackContent />
      </Suspense>
    </div>
  );
}