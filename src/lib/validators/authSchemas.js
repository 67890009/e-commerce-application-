import { z } from "zod";

// ---- Shared field-level rules (reused across schemas) ----

const emailField = z
  .string()
  .trim()
  .min(1, "Email is required")
  .email("Enter a valid email address");

const passwordField = z
  .string()
  .min(8, "Password must be at least 8 characters")
  .regex(/[A-Z]/, "Password must contain at least one uppercase letter")
  .regex(/[0-9]/, "Password must contain at least one number")
  .regex(/[^A-Za-z0-9]/, "Password must contain at least one special character");

const fullNameField = z
  .string()
  .trim()
  .min(2, "Name must be at least 2 characters")
  .max(100, "Name must be under 100 characters");

const phoneField = z
  .string()
  .trim()
  .regex(/^\+[1-9]\d{7,14}$/, "Enter a valid phone number in international format (e.g. +919876543210)");

const otpField = z
  .string()
  .length(6, "OTP must be exactly 6 digits")
  .regex(/^\d{6}$/, "OTP must contain only numbers");

// ---- Register ----
// role is restricted to customer/seller at the schema level —
// admin can never be selected, matching the API contract rule.

export const registerSchema = z
  .object({
    full_name: fullNameField,
    email: emailField,
    password: passwordField,
    confirm_password: z.string(),
    role: z.enum(["customer", "seller"], {
      errorMap: () => ({ message: "Select whether you're registering as a Customer or Seller" }),
    }),
    // required only when role === "seller" — refined below
    business_name: z.string().trim().optional(),
  })
  .refine((data) => data.password === data.confirm_password, {
    message: "Passwords do not match",
    path: ["confirm_password"],
  })
  .refine(
    (data) => data.role !== "seller" || (data.business_name && data.business_name.length >= 2),
    {
      message: "Business name is required for seller accounts",
      path: ["business_name"],
    }
  );

// ---- Login ----

export const loginSchema = z.object({
  email: emailField,
  password: z.string().min(1, "Password is required"),
});

// ---- OTP ----

export const otpSendSchema = z.object({
  phone: phoneField,
});

export const otpVerifySchema = z.object({
  phone: phoneField,
  otp: otpField,
});

// ---- Google OAuth callback exchange (internal use, not a user-facing form) ----

export const googleExchangeSchema = z.object({
  code: z.string().min(1, "Missing authorization code"),
});

// ---- Admin: reject seller (optional reason) ----

export const rejectSellerSchema = z.object({
  reason: z.string().trim().max(500, "Reason must be under 500 characters").optional(),
});