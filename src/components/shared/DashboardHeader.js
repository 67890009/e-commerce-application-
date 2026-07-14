// src/components/shared/DashboardHeader.js
"use client";

import { useDispatch, useSelector } from "react-redux";
import { useRouter } from "next/navigation";
import { selectCurrentUser, logoutUser } from "@/features/auth/authSlice";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

export default function DashboardHeader({ title }) {
  const user = useSelector(selectCurrentUser);
  const dispatch = useDispatch();
  const router = useRouter();

  const handleLogout = async () => {
    await dispatch(logoutUser());
    router.push("/login");
  };

  return (
    <div className="flex items-center justify-between border-b pb-4 mb-6">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <h1 className="text-xl font-semibold tracking-tight">{title}</h1>
          <Badge variant="secondary" className="capitalize">{user?.role}</Badge>
        </div>
        <p className="text-sm text-muted-foreground">
          {user?.full_name} · {user?.email}
        </p>
      </div>
      <Button variant="outline" onClick={handleLogout}>
        Log out
      </Button>
    </div>
  );
}