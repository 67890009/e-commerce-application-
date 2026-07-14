// src/lib/refreshTokenStorage.js

const REFRESH_TOKEN_KEY = "refresh_token";

export function getRefreshToken() {
  if (typeof window === "undefined") return null;
  return sessionStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token) {
  if (typeof window === "undefined") return;
  sessionStorage.setItem(REFRESH_TOKEN_KEY, token);
}

export function clearRefreshToken() {
  if (typeof window === "undefined") return;
  sessionStorage.removeItem(REFRESH_TOKEN_KEY);
}