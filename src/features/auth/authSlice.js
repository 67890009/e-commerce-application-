// src/features/auth/authSlice.js
import { setAccessTokenForRequests } from "@/lib/axios";
import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import * as authApi from "@/services/authService";
import {
  getRefreshToken,
  setRefreshToken,
  clearRefreshToken,
} from "@/lib/refreshTokenStorage";

// =====================================================================
// Thunks
// =====================================================================

function persistTokens({ access_token, refresh_token }) {
  setRefreshToken(refresh_token);
  return access_token;
}

export const registerUser = createAsyncThunk(
  "auth/register",
  async (payload, { rejectWithValue }) => {
    try {
      return await authApi.register(payload);
    } catch (err) {
      return rejectWithValue(err.data?.message || "Registration failed");
    }
  }
);

export const loginUser = createAsyncThunk(
  "auth/login",
  async (payload, { rejectWithValue }) => {
    try {
      const res = await authApi.login(payload);
      const accessToken = persistTokens(res);
      setAccessTokenForRequests(accessToken);
      return { user: res.user, accessToken };
    } catch (err) {
       return rejectWithValue(err.data?.message || "Login failed");
    }
  }
);

export const sendOtp = createAsyncThunk(
  "auth/sendOtp",
  async (payload, { rejectWithValue }) => {
    try {
      return await authApi.otpSend(payload);
    } catch (err) {
      return rejectWithValue(err.data?.message || "Failed to send OTP");
    }
  }
);

export const verifyOtp = createAsyncThunk(
  "auth/verifyOtp",
  async (payload, { rejectWithValue }) => {
    try {
      const res = await authApi.otpVerify(payload);
      const accessToken = persistTokens(res);
      setAccessTokenForRequests(accessToken);
      return { user: res.user, accessToken };
    } catch (err) {
      return rejectWithValue(err.data?.message || "OTP verification failed");
    }
  }
);

export const googleExchange = createAsyncThunk(
  "auth/googleExchange",
  async (payload, { rejectWithValue }) => {
    try {
      const res = await authApi.googleExchange(payload);
      const accessToken = persistTokens(res);
      setAccessTokenForRequests(accessToken);
      return { user: res.user, accessToken };
    } catch (err) {
      return rejectWithValue(err.data?.message || "Google sign-in failed");
    }
  }
);

// Called on app load to silently restore a session from the refresh token.
// If there's no refresh token, or it's invalid, resolves to "not logged in"
// without throwing a visible error — this is a background bootstrap, not a
// user-initiated action.
export const bootstrapAuth = createAsyncThunk(
  "auth/bootstrap",
  async (_, { rejectWithValue }) => {
    const refresh_token = getRefreshToken();
    if (!refresh_token) {
      return rejectWithValue(null); // silent — no session to restore
    }
    try {
      const tokenRes = await authApi.refresh({ refresh_token });
      setRefreshToken(tokenRes.refresh_token); // rotation — store the NEW one
      setAccessTokenForRequests(tokenRes.access_token);
      const user = await authApi.getMe({ access_token: tokenRes.access_token });
      return { user, accessToken: tokenRes.access_token };
    } catch (err) {
      clearRefreshToken(); // stale/invalid — don't keep retrying with it
      return rejectWithValue(null);
    }
  }
);

export const logoutUser = createAsyncThunk("auth/logout", async () => {
  const refresh_token = getRefreshToken();
  if (refresh_token) {
    try {
      await authApi.logout({ refresh_token });
    } catch {
      // even if the backend call fails, we still clear local state below
    }
  }
  clearRefreshToken();
  setAccessTokenForRequests(null);
  return null;
});

// =====================================================================
// Slice
// =====================================================================

const initialState = {
  user: null, // { id, full_name, email, role, is_verified, seller_approved, business_name }
  accessToken: null, // in-memory ONLY — never persisted, per agreed security model
  status: "idle", // 'idle' | 'loading' | 'succeeded' | 'failed'
  error: null,
  isInitializing: true, // true until bootstrapAuth resolves once on app load
};

const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    clearAuthError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // ---- Register ----
      .addCase(registerUser.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(registerUser.fulfilled, (state) => {
        state.status = "succeeded";
        // No tokens issued here — user must verify email (Customer) or
        // wait for admin approval (Seller) before logging in.
      })
      .addCase(registerUser.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })

      // ---- Login ----
      .addCase(loginUser.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(loginUser.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.user = action.payload.user;
        state.accessToken = action.payload.accessToken;
      })
      .addCase(loginUser.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })

      // ---- OTP verify (login or auto-register) ----
      .addCase(verifyOtp.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(verifyOtp.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.user = action.payload.user;
        state.accessToken = action.payload.accessToken;
      })
      .addCase(verifyOtp.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })

      // ---- Google OAuth ----
      .addCase(googleExchange.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(googleExchange.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.user = action.payload.user;
        state.accessToken = action.payload.accessToken;
      })
      .addCase(googleExchange.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })

      // ---- Bootstrap (silent session restore on app load) ----
      .addCase(bootstrapAuth.pending, (state) => {
        state.isInitializing = true;
      })
      .addCase(bootstrapAuth.fulfilled, (state, action) => {
        state.isInitializing = false;
        state.user = action.payload.user;
        state.accessToken = action.payload.accessToken;
      })
      .addCase(bootstrapAuth.rejected, (state) => {
        state.isInitializing = false;
        // no user/accessToken — simply not logged in, not an error to show
      })

      // ---- Logout ----
      .addCase(logoutUser.fulfilled, (state) => {
        state.user = null;
        state.accessToken = null;
        state.status = "idle";
        state.error = null;
      });
  },
});

export const { clearAuthError } = authSlice.actions;
export default authSlice.reducer;

// =====================================================================
// Selectors
// =====================================================================

export const selectCurrentUser = (state) => state.auth.user;
export const selectAccessToken = (state) => state.auth.accessToken;
export const selectIsAuthenticated = (state) => Boolean(state.auth.user);
export const selectAuthStatus = (state) => state.auth.status;
export const selectAuthError = (state) => state.auth.error;
export const selectIsInitializing = (state) => state.auth.isInitializing;

// Derived: does the logged-in seller still need to wait for approval?
export const selectIsPendingSeller = (state) => {
  const user = state.auth.user;
  return Boolean(user && user.role === "seller" && user.seller_approved === false);
};