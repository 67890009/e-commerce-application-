// src/services/authService.js
//
// Single import point for the rest of the app. Swaps mock <-> real based
// on an env var — no component or Redux file should ever import
// services/mock or services/real directly again after this.

const USE_MOCK = process.env.NEXT_PUBLIC_USE_MOCK_AUTH !== "false"; // defaults to mock

const impl = USE_MOCK
  ? await import("@/services/mock/authService.mock")
  : await import("@/services/real/authService.real");

export const {
  register,
  login,
  otpSend,
  otpVerify,
  googleExchange,
  refresh,
  logout,
  getMe,
  adminListPendingSellers,
  adminApproveSeller,
  adminRejectSeller,
} = impl;