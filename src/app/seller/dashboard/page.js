// src/app/seller/dashboard/page.js
"use client";

import RouteGuard from "@/components/auth/RouteGuard";
import DashboardHeader from "@/components/shared/DashboardHeader";

export default function SellerDashboardPage() {
  return (
    <RouteGuard allowedRoles={["seller"]} requireSellerApproved>
      <div className="max-w-3xl mx-auto px-6 py-10">
        <DashboardHeader title="Seller Dashboard" />
        <div className="rounded-lg border p-6 space-y-2">
          <p className="text-sm text-muted-foreground">
            You&apos;re logged in as an approved Seller. Product listings,
            orders, and inventory management will be built here.
          </p>
        </div>
      </div>
    </RouteGuard>
  );
}