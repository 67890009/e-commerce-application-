// src/features/admin/sellersSlice.js

import { createSlice, createAsyncThunk } from "@reduxjs/toolkit";
import * as authApi from "@/services/authService";

export const fetchPendingSellers = createAsyncThunk(
  "sellers/fetchPending",
  async (_, { getState, rejectWithValue }) => {
    try {
      const access_token = getState().auth.accessToken;
      return await authApi.adminListPendingSellers({ access_token });
    } catch (err) {
      return rejectWithValue(err.data?.message || "Failed to load pending sellers");
    }
  }
);

export const approveSeller = createAsyncThunk(
  "sellers/approve",
  async (seller_id, { getState, rejectWithValue }) => {
    try {
      const access_token = getState().auth.accessToken;
      await authApi.adminApproveSeller({ access_token, seller_id });
      return seller_id;
    } catch (err) {
      return rejectWithValue(err.data?.message || "Failed to approve seller");
    }
  }
);

export const rejectSeller = createAsyncThunk(
  "sellers/reject",
  async ({ seller_id, reason }, { getState, rejectWithValue }) => {
    try {
      const access_token = getState().auth.accessToken;
      await authApi.adminRejectSeller({ access_token, seller_id, reason });
      return seller_id;
    } catch (err) {
      return rejectWithValue(err.data?.message || "Failed to reject seller");
    }
  }
);

const initialState = {
  pendingSellers: [],
  total: 0,
  status: "idle",
  error: null,
  actionStatus: {}, // { [seller_id]: "approving" | "rejecting" } — per-row loading state
};

const sellersSlice = createSlice({
  name: "sellers",
  initialState,
  reducers: {
    clearSellersError(state) {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPendingSellers.pending, (state) => {
        state.status = "loading";
        state.error = null;
      })
      .addCase(fetchPendingSellers.fulfilled, (state, action) => {
        state.status = "succeeded";
        state.pendingSellers = action.payload.sellers;
        state.total = action.payload.total;
      })
      .addCase(fetchPendingSellers.rejected, (state, action) => {
        state.status = "failed";
        state.error = action.payload;
      })

      .addCase(approveSeller.pending, (state, action) => {
        state.actionStatus[action.meta.arg] = "approving";
      })
      .addCase(approveSeller.fulfilled, (state, action) => {
        delete state.actionStatus[action.payload];
        // Remove from list immediately — no need to refetch the whole list
        state.pendingSellers = state.pendingSellers.filter((s) => s.id !== action.payload);
        state.total -= 1;
      })
      .addCase(approveSeller.rejected, (state, action) => {
        delete state.actionStatus[action.meta.arg];
        state.error = action.payload;
      })

      .addCase(rejectSeller.pending, (state, action) => {
        state.actionStatus[action.meta.arg.seller_id] = "rejecting";
      })
      .addCase(rejectSeller.fulfilled, (state, action) => {
        delete state.actionStatus[action.payload];
        state.pendingSellers = state.pendingSellers.filter((s) => s.id !== action.payload);
        state.total -= 1;
      })
      .addCase(rejectSeller.rejected, (state, action) => {
        delete state.actionStatus[action.meta.arg.seller_id];
        state.error = action.payload;
      });
  },
});

export const { clearSellersError } = sellersSlice.actions;
export default sellersSlice.reducer;

export const selectPendingSellers = (state) => state.sellers.pendingSellers;
export const selectSellersStatus = (state) => state.sellers.status;
export const selectSellersError = (state) => state.sellers.error;
export const selectSellerActionStatus = (sellerId) => (state) => state.sellers.actionStatus[sellerId];