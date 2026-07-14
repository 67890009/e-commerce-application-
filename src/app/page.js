// src/app/page.js
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSelector } from "react-redux";
import {
  selectCurrentUser,
  selectIsAuthenticated,
  selectIsInitializing,
} from "@/features/auth/authSlice";
import DashboardHeader from "@/components/shared/DashboardHeader";

export default function HomePage() {
  const router = useRouter();
  const user = useSelector(selectCurrentUser);
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const isInitializing = useSelector(selectIsInitializing);

  useEffect(() => {
    if (isInitializing) return; // wait for session restore to resolve

    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    // Seller/Admin have their own dedicated dashboards — bounce them there
    // if they land on "/" directly, so "/" is effectively the Customer home.
    if (user.role === "admin") {
      router.replace("/admin/dashboard");
    } else if (user.role === "seller") {
      router.replace(user.seller_approved ? "/seller/dashboard" : "/seller/pending");
    }
  }, [isInitializing, isAuthenticated, user, router]);

  if (isInitializing || !isAuthenticated || user?.role !== "customer") {
    return null; // avoid flashing content during redirect checks
  }

  return (
    <div className="max-w-3xl mx-auto px-6 py-10">
      <DashboardHeader title="Customer Account" />
      <div className="rounded-lg border p-6 space-y-2">
        <p className="text-sm text-muted-foreground">
          You&apos;re logged in as a Customer. Product browsing, cart, and
          checkout will be built here as the Homepage feature.
        </p>
      </div>
    </div>
  );
}