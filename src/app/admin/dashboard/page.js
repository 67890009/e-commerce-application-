// src/app/admin/dashboard/page.js
"use client";

import RouteGuard from "@/components/auth/RouteGuard";
import DashboardHeader from "@/components/shared/DashboardHeader";
import PendingSellersList from "@/components/admin/PendingSellersList";

export default function AdminDashboardPage() {
  return (
    <RouteGuard allowedRoles={["admin"]}>
      <div className="max-w-3xl mx-auto px-6 py-10 space-y-6">
        <DashboardHeader title="Admin Dashboard" />
        <div className="space-y-1">
          <h2 className="text-lg font-semibold tracking-tight">Seller Applications</h2>
          <p className="text-sm text-muted-foreground">
            Review and approve or reject pending seller registrations.
          </p>
        </div>
        <PendingSellersList />
      </div>
    </RouteGuard>
  );
}