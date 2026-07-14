// src/lib/axios.js

import axios from "axios";
import { getRefreshToken, setRefreshToken, clearRefreshToken } from "@/lib/refreshTokenStorage";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Access token is kept in Redux memory, not here — but axios needs a way
// to read it for the Authorization header without importing the store
// directly into this file (avoids a circular import: store -> slice ->
// this file -> store). Instead, the store injects it via this setter,
// called once when the app boots and again on every login/refresh.
let currentAccessToken = null;
export function setAccessTokenForRequests(token) {
  currentAccessToken = token;
}

apiClient.interceptors.request.use((config) => {
  if (currentAccessToken) {
    config.headers.Authorization = `Bearer ${currentAccessToken}`;
  }
  return config;
});

// Auto-refresh on 401: try once to get a new access token via the refresh
// token, retry the original request, and only force logout if that also
// fails. Prevents users getting kicked out just because their 7-min access
// token expired mid-session.
let isRefreshing = false;
let refreshQueue = [];

function processQueue(error, token = null) {
  refreshQueue.forEach(({ resolve, reject }) => {
    if (error) reject(error);
    else resolve(token);
  });
  refreshQueue = [];
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status !== 401 || originalRequest._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Another request already triggered a refresh — queue this one
      // instead of firing a second parallel refresh call.
      return new Promise((resolve, reject) => {
        refreshQueue.push({ resolve, reject });
      })
        .then((token) => {
          originalRequest.headers.Authorization = `Bearer ${token}`;
          return apiClient(originalRequest);
        })
        .catch((err) => Promise.reject(err));
    }

    originalRequest._retry = true;
    isRefreshing = true;

    const refresh_token = getRefreshToken();
    if (!refresh_token) {
      isRefreshing = false;
      clearRefreshToken();
      return Promise.reject(error);
    }

    try {
      const { data } = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
        refresh_token,
      });
      setRefreshToken(data.refresh_token); // rotation — store the NEW one
      setAccessTokenForRequests(data.access_token);
      processQueue(null, data.access_token);
      originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
      return apiClient(originalRequest);
    } catch (refreshError) {
      processQueue(refreshError, null);
      clearRefreshToken();
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

export default apiClient;