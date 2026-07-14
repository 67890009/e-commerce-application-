// src/store/store.js

import { configureStore } from "@reduxjs/toolkit";
import authReducer from "@/features/auth/authSlice";
import sellersReducer from "@/features/admin/sellersSlice";

export const store = configureStore({
  reducer: {
    auth: authReducer,
    sellers: sellersReducer,
  },
});