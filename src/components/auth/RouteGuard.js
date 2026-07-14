// src/components/auth/RouteGuard.js
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useSelector } from "react-redux";
import {
  selectCurrentUser,
  selectIsInitializing,
  selectIsAuthenticated,
} from "@/features/auth/authSlice";

/**
 * Client-side route guard. NOT a security boundary — see note in chat.
 * Prevents wrong content flashing/rendering for the wrong role in normal
 * app usage. Real enforcement must happen on the backend per-endpoint.
 *
 * Props:
 *  - allowedRoles: array, e.g. ["admin"] or ["seller"]
 *  - requireSellerApproved: bool — if true, unapproved sellers get bounced
 *    to /seller/pending instead of being let through
 *  - children: the actual page content
 */
export default function RouteGuard({ allowedRoles, requireSellerApproved = false, children }) {
  const router = useRouter();
  const user = useSelector(selectCurrentUser);
  const isAuthenticated = useSelector(selectIsAuthenticated);
  const isInitializing = useSelector(selectIsInitializing);

  useEffect(() => {
    // Wait for bootstrapAuth to resolve — otherwise we'd redirect to /login
    // on every page refresh before the session has a chance to restore.
    if (isInitializing) return;

    if (!isAuthenticated) {
      router.replace("/login");
      return;
    }

    if (allowedRoles && !allowedRoles.includes(user.role)) {
      // Logged in, but wrong role for this route — send them somewhere
      // sane for THEIR role rather than a generic error page.
      if (user.role === "admin") router.replace("/admin/dashboard");
      else if (user.role === "seller") {
        router.replace(user.seller_approved ? "/seller/dashboard" : "/seller/pending");
      } else router.replace("/");
      return;
    }

    if (requireSellerApproved && user.role === "seller" && !user.seller_approved) {
      router.replace("/seller/pending");
    }
  }, [isInitializing, isAuthenticated, user, allowedRoles, requireSellerApproved, router]);

  // While we don't know yet, or a redirect is about to happen, render
  // nothing rather than a flash of protected content.
  if (isInitializing || !isAuthenticated) return null;
  if (allowedRoles && !allowedRoles.includes(user.role)) return null;
  if (requireSellerApproved && user.role === "seller" && !user.seller_approved) return null;

  return children;
}