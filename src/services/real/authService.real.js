// src/services/real/authService.real.js
//
// Real backend implementation, matching authService.mock.js function-for-
// function. Every function here must accept the same params and return/
// throw the same shape as its mock counterpart — that's what makes the
// swap in services/authService.js invisible to the rest of the app.

import apiClient from "@/lib/axios";

function normalizeError(error) {
  // Axios errors nest status/data under `error.response` — flatten to
  // match the mock's ApiError shape (`error.status`, `error.data`) so
  // authSlice.js doesn't need to know which service it's talking to.
  const err = new Error(error.response?.data?.message || "Request failed");
  err.status = error.response?.status;
  err.data = error.response?.data;
  throw err;
}

export async function register(payload) {
  try {
    const { data } = await apiClient.post("/api/v1/auth/register", payload);
    return data;
  } catch (error) {
    normalizeError(error);
  }
}

export async function login(payload) {
  try {
    const { data } = await apiClient.post("/api/v1/auth/login", payload);
    return data;
  } catch (error) {
    normalizeError(error);
  }
}

export async function otpSend(payload) {
  try {
    const { data } = await apiClient.post("/api/v1/auth/otp/send", payload);
    return data;
  } catch (error) {
    normalizeError(error);
  }
}

export async function otpVerify(payload) {
  try {
    const { data } = await apiClient.post("/api/v1/auth/otp/verify", payload);
    return data;
  } catch (error) {
    normalizeError(error);
  }
}

export async function googleExchange(payload) {
  try {
    const { data } = await apiClient.post("/api/v1/auth/google/exchange", payload);
    return data;
  } catch (error) {
    normalizeError(error);
  }
}

export async function refresh(payload) {
  try {
    const { data } = await apiClient.post("/api/v1/auth/refresh", payload);
    return data;
  } catch (error) {
    normalizeError(error);
  }
}

export async function logout(payload) {
  try {
    await apiClient.post("/api/v1/auth/logout", payload);
    return null;
  } catch (error) {
    normalizeError(error);
  }
}

export async function getMe() {
  // access_token not passed explicitly — apiClient's interceptor attaches
  // it automatically via the Authorization header.
  try {
    const { data } = await apiClient.get("/api/v1/auth/me");
    return data;
  } catch (error) {
    normalizeError(error);
  }
}

export async function adminListPendingSellers() {
  try {
    const { data } = await apiClient.get("/api/v1/admin/sellers/pending");
    return data;
  } catch (error) {
    normalizeError(error);
  }
}

export async function adminApproveSeller({ seller_id }) {
  try {
    const { data } = await apiClient.post(`/api/v1/admin/sellers/${seller_id}/approve`);
    return data;
  } catch (error) {
    normalizeError(error);
  }
}

export async function adminRejectSeller({ seller_id, reason }) {
  try {
    const { data } = await apiClient.post(`/api/v1/admin/sellers/${seller_id}/reject`, { reason });
    return data;
  } catch (error) {
    normalizeError(error);
  }
}