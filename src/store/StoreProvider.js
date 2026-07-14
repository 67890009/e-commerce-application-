// src/store/StoreProvider.js
"use client";

import { useEffect, useRef } from "react";
import { Provider } from "react-redux";
import { store } from "@/store/store";
import { bootstrapAuth } from "@/features/auth/authSlice";

export default function StoreProvider({ children }) {
  const initialized = useRef(false);

  useEffect(() => {
    // Guard against double-dispatch in React 18 StrictMode (dev only,
    // effects run twice) — bootstrapAuth rotates the refresh token, so
    // running it twice would burn the second call unnecessarily.
    if (initialized.current) return;
    initialized.current = true;

    store.dispatch(bootstrapAuth());
  }, []);

  return <Provider store={store}>{children}</Provider>;
}