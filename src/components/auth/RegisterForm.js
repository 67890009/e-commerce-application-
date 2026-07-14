// src/components/auth/RegisterForm.js
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useDispatch, useSelector } from "react-redux";

import { registerSchema } from "@/lib/validators/authSchemas";
import { registerUser, selectAuthStatus, selectAuthError, clearAuthError } from "@/features/auth/authSlice";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

export default function RegisterForm() {
  const router = useRouter();
  const dispatch = useDispatch();
  const status = useSelector(selectAuthStatus);
  const serverError = useSelector(selectAuthError);
  const [role, setRole] = useState("customer");

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      full_name: "",
      email: "",
      password: "",
      confirm_password: "",
      role: "customer",
      business_name: "",
    },
  });

  const handleRoleChange = (value) => {
    setRole(value);
    setValue("role", value, { shouldValidate: true });
  };

  const onSubmit = async (data) => {
    dispatch(clearAuthError());
    const result = await dispatch(registerUser(data));

    if (registerUser.fulfilled.match(result)) {
      const redirectType = data.role === "seller" ? "seller" : "customer";
      router.push(`/register/success?type=${redirectType}`);
    }
    // rejected case: serverError is already in Redux state, rendered below
  };

  const isSubmitting = status === "loading";

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 w-full max-w-md">
      {serverError && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {serverError}
        </div>
      )}

      {/* Role selection FIRST — it changes which fields appear below */}
      <div className="space-y-2">
        <Label htmlFor="role">I want to register as</Label>
        <Select value={role} onValueChange={handleRoleChange}>
          <SelectTrigger id="role">
            <SelectValue placeholder="Select account type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="customer">Customer</SelectItem>
            <SelectItem value="seller">Seller</SelectItem>
          </SelectContent>
        </Select>
        {errors.role && <p className="text-sm text-red-600">{errors.role.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="full_name">Full name</Label>
        <Input id="full_name" {...register("full_name")} placeholder="Jane Doe" />
        {errors.full_name && <p className="text-sm text-red-600">{errors.full_name.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" {...register("email")} placeholder="you@example.com" />
        {errors.email && <p className="text-sm text-red-600">{errors.email.message}</p>}
      </div>

      {role === "seller" && (
        <div className="space-y-2">
          <Label htmlFor="business_name">Business name</Label>
          <Input id="business_name" {...register("business_name")} placeholder="Your Store LLC" />
          {errors.business_name && (
            <p className="text-sm text-red-600">{errors.business_name.message}</p>
          )}
        </div>
      )}

      <div className="space-y-2">
        <Label htmlFor="password">Password</Label>
        <Input id="password" type="password" {...register("password")} />
        {errors.password && <p className="text-sm text-red-600">{errors.password.message}</p>}
      </div>

      <div className="space-y-2">
        <Label htmlFor="confirm_password">Confirm password</Label>
        <Input id="confirm_password" type="password" {...register("confirm_password")} />
        {errors.confirm_password && (
          <p className="text-sm text-red-600">{errors.confirm_password.message}</p>
        )}
      </div>

      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "Creating account..." : "Create account"}
      </Button>

      {role === "seller" && (
        <p className="text-xs text-muted-foreground text-center">
          Seller accounts require admin approval before you can start selling.
        </p>
      )}
    </form>
  );
}