// src/app/seller/pending/page.js
"use client";

import { useSelector, useDispatch } from "react-redux";
import { useRouter } from "next/navigation";
import { selectCurrentUser, logoutUser } from "@/features/auth/authSlice";
import { Button } from "@/components/ui/button";

export default function SellerPendingPage() {
  const user = useSelector(selectCurrentUser);
  const dispatch = useDispatch();
  const router = useRouter();

  const handleLogout = async () => {
    await dispatch(logoutUser());
    router.push("/login");
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-6">
      <div className="max-w-md w-full text-center space-y-6">
        <div className="mx-auto w-14 h-14 rounded-full bg-amber-100 flex items-center justify-center">
          <svg className="w-7 h-7 text-amber-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">
            Application under review
          </h1>
          <p className="text-sm text-muted-foreground">
            Hi {user?.full_name?.split(" ")[0] || "there"}, your seller account
            for <span className="font-medium">{user?.business_name}</span> is
            still being reviewed by our team. We&apos;ll email you at{" "}
            <span className="font-medium">{user?.email}</span> as soon as
            you&apos;re approved.
          </p>
        </div>

        <Button variant="outline" onClick={handleLogout} className="w-full">
          Log out
        </Button>
      </div>
    </div>
  );
}