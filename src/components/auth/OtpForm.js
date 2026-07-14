// src/components/auth/OtpForm.js
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useDispatch, useSelector } from "react-redux";

import { otpSendSchema, otpVerifySchema } from "@/lib/validators/authSchemas";
import {
  sendOtp,
  verifyOtp,
  selectAuthStatus,
  selectAuthError,
  clearAuthError,
} from "@/features/auth/authSlice";
import { getPostLoginRedirect } from "@/components/auth/LoginForm";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  InputOTP,
  InputOTPGroup,
  InputOTPSlot,
} from "@/components/ui/input-otp";

const RESEND_COOLDOWN_SECONDS = 30;

export default function OtpForm() {
  const router = useRouter();
  const dispatch = useDispatch();
  const status = useSelector(selectAuthStatus);
  const serverError = useSelector(selectAuthError);

  const [step, setStep] = useState("phone"); // "phone" | "otp"
  const [phone, setPhone] = useState("");
  const [otpValue, setOtpValue] = useState("");
  const [cooldown, setCooldown] = useState(0);

  const phoneForm = useForm({
    resolver: zodResolver(otpSendSchema),
    defaultValues: { phone: "" },
  });

  const startCooldown = () => {
    setCooldown(RESEND_COOLDOWN_SECONDS);
    const interval = setInterval(() => {
      setCooldown((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleSendOtp = async (data) => {
    dispatch(clearAuthError());
    const result = await dispatch(sendOtp({ phone: data.phone }));

    if (sendOtp.fulfilled.match(result)) {
      setPhone(data.phone);
      setStep("otp");
      startCooldown();
    }
  };

  const handleResend = async () => {
    if (cooldown > 0) return;
    dispatch(clearAuthError());
    const result = await dispatch(sendOtp({ phone }));
    if (sendOtp.fulfilled.match(result)) {
      startCooldown();
    }
  };

  const handleVerify = async () => {
    dispatch(clearAuthError());

    const parsed = otpVerifySchema.safeParse({ phone, otp: otpValue });
    if (!parsed.success) {
      // Rare — InputOTP already constrains to 6 digits, but guard anyway
      return;
    }

    const result = await dispatch(verifyOtp({ phone, otp: otpValue }));
    if (verifyOtp.fulfilled.match(result)) {
      const redirectPath = getPostLoginRedirect(result.payload.user);
      router.push(redirectPath);
    }
  };

  const isSubmitting = status === "loading";

  if (step === "phone") {
    return (
      <form onSubmit={phoneForm.handleSubmit(handleSendOtp)} className="space-y-5 w-full max-w-md">
        {serverError && (
          <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
            {serverError}
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="phone">Phone number</Label>
          <Input
            id="phone"
            type="tel"
            placeholder="+919876543210"
            {...phoneForm.register("phone")}
          />
          {phoneForm.formState.errors.phone && (
            <p className="text-sm text-red-600">{phoneForm.formState.errors.phone.message}</p>
          )}
          <p className="text-xs text-muted-foreground">
            Include your country code, e.g. +91 for India.
          </p>
        </div>

        <Button type="submit" className="w-full" disabled={isSubmitting}>
          {isSubmitting ? "Sending code..." : "Send code"}
        </Button>
      </form>
    );
  }

  // step === "otp"
  return (
    <div className="space-y-5 w-full max-w-md">
      {serverError && (
        <div className="rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {serverError}
        </div>
      )}

      <div className="space-y-2 text-center">
        <p className="text-sm text-muted-foreground">
          Enter the 6-digit code sent to <span className="font-medium">{phone}</span>
        </p>
      </div>

      <div className="flex justify-center">
        <InputOTP maxLength={6} value={otpValue} onChange={setOtpValue}>
          <InputOTPGroup>
            <InputOTPSlot index={0} />
            <InputOTPSlot index={1} />
            <InputOTPSlot index={2} />
            <InputOTPSlot index={3} />
            <InputOTPSlot index={4} />
            <InputOTPSlot index={5} />
          </InputOTPGroup>
        </InputOTP>
      </div>

      <Button
        onClick={handleVerify}
        className="w-full"
        disabled={isSubmitting || otpValue.length !== 6}
      >
        {isSubmitting ? "Verifying..." : "Verify code"}
      </Button>

      <div className="text-sm text-center text-muted-foreground">
        {cooldown > 0 ? (
          <span>Resend code in {cooldown}s</span>
        ) : (
          <button type="button" onClick={handleResend} className="underline underline-offset-4">
            Resend code
          </button>
        )}
      </div>

      <button
        type="button"
        onClick={() => {
          setStep("phone");
          dispatch(clearAuthError());
        }}
        className="text-xs text-muted-foreground underline underline-offset-4 block mx-auto"
      >
        Use a different number
      </button>
    </div>
  );
}