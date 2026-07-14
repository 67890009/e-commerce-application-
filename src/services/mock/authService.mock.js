// src/services/mock/authService.mock.js
//
// In-memory mock backend for Auth. Simulates network delay, validation,
// and error responses matching the real API contract exactly.
// Data resets on page refresh — that's expected for a mock.

// ---- Custom error shape, mimics an Axios error response ----
// Real Axios errors expose `error.response.status` and `error.response.data`.
// We normalize to `error.status` / `error.data` here and will do the same
// unwrapping in the real service later, so calling code never needs to know
// which one it's talking to.

class ApiError extends Error {
  constructor(status, data) {
    super(data?.message || "Request failed");
    this.status = status;
    this.data = data;
  }
}

// ---- Fake network latency, makes loading states feel real during dev ----

const delay = (ms = 500) => new Promise((resolve) => setTimeout(resolve, ms));

// ---- In-memory "database" ----

let mockUsers = [
  // Seed one admin so you can test admin login without a registration path
  // (matches the rule: admin is never self-registered).
  {
    id: "admin-seed-0001",
    full_name: "Platform Admin",
    email: "admin@marketplace.test",
    password: "Admin@123",
    role: "admin",
    is_verified: true,
    seller_approved: null,
    business_name: null,
    phone: null,
    created_at: new Date().toISOString(),
  },
];

let otpStore = new Map(); // phone -> { otp, expiresAt }
let accessTokenStore = new Map(); // token -> { userId, expiresAt }
let refreshTokenStore = new Map(); // token -> { userId, used }

let userIdCounter = 1;
const generateId = () => `user-${Date.now()}-${userIdCounter++}`;
const generateToken = (prefix) =>
  `${prefix}-${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;

const ACCESS_TOKEN_TTL_SECONDS = 420; // 7 minutes, confirmed with backend

// ---- Helpers ----

function sanitizeUser(user) {
  const { password, ...safe } = user;
  return safe;
}

function issueTokenPair(user) {
  const access_token = generateToken("access");
  const refresh_token = generateToken("refresh");

  accessTokenStore.set(access_token, {
    userId: user.id,
    expiresAt: Date.now() + ACCESS_TOKEN_TTL_SECONDS * 1000,
  });
  refreshTokenStore.set(refresh_token, { userId: user.id, used: false });

  return { access_token, refresh_token, expires_in: ACCESS_TOKEN_TTL_SECONDS };
}

function buildAuthResponse(user) {
  return {
    user: sanitizeUser(user),
    ...issueTokenPair(user),
  };
}

function findUserByEmail(email) {
  return mockUsers.find((u) => u.email.toLowerCase() === email.toLowerCase());
}

function findUserByPhone(phone) {
  return mockUsers.find((u) => u.phone === phone);
}

function getUserFromAccessToken(token) {
  const entry = accessTokenStore.get(token);
  if (!entry) throw new ApiError(401, { message: "Invalid or expired access token" });
  if (Date.now() > entry.expiresAt) {
    accessTokenStore.delete(token);
    throw new ApiError(401, { message: "Access token expired" });
  }
  const user = mockUsers.find((u) => u.id === entry.userId);
  if (!user) throw new ApiError(401, { message: "User not found" });
  return user;
}

function requireAdmin(accessToken) {
  const user = getUserFromAccessToken(accessToken);
  if (user.role !== "admin") {
    throw new ApiError(403, { message: "Admin access required" });
  }
  return user;
}

// =====================================================================
// 1. Register (Customer instant / Seller pending approval)
// =====================================================================

export async function register({ full_name, email, password, role, business_name }) {
  await delay();

  if (role === "admin") {
    throw new ApiError(422, { message: "Admin accounts cannot self-register" });
  }

  if (findUserByEmail(email)) {
    throw new ApiError(409, { message: "Email already registered" });
  }

  const user = {
    id: generateId(),
    full_name,
    email,
    password, // mock only — real backend hashes this, never stored plain
    role,
    is_verified: false, // email verification required before login
    seller_approved: role === "seller" ? false : null,
    business_name: role === "seller" ? business_name : null,
    phone: null,
    created_at: new Date().toISOString(),
  };

  mockUsers.push(user);

  // Real backend sends a verification email here.
  // For mock/dev convenience, auto-verify after 3s so you're not stuck.
  setTimeout(() => {
    const stored = mockUsers.find((u) => u.id === user.id);
    if (stored) stored.is_verified = true;
  }, 3000);

  return { user: sanitizeUser(user), message: "Registered. Check your email to verify your account." };
}

// =====================================================================
// 2. Login (email + password)
// =====================================================================

export async function login({ email, password }) {
  await delay();

  const user = findUserByEmail(email);
  if (!user || user.password !== password) {
    throw new ApiError(401, { message: "Invalid email or password" });
  }

  if (!user.is_verified) {
    throw new ApiError(403, { message: "Please verify your email before logging in." });
  }

  return buildAuthResponse(user);
}

// =====================================================================
// 3 & 4. Phone OTP — send + verify
// =====================================================================

export async function otpSend({ phone }) {
  await delay(300);

  const otp = "123456"; // fixed for mock/dev — check console log below
  otpStore.set(phone, { otp, expiresAt: Date.now() + 5 * 60 * 1000 });

  console.info(`[MOCK OTP] Sent OTP ${otp} to ${phone}`);
  return { message: "OTP sent", expires_in: 300 };
}

export async function otpVerify({ phone, otp }) {
  await delay();

  const entry = otpStore.get(phone);
  if (!entry || entry.otp !== otp) {
    throw new ApiError(400, { message: "Invalid OTP" });
  }
  if (Date.now() > entry.expiresAt) {
    otpStore.delete(phone);
    throw new ApiError(400, { message: "OTP expired" });
  }

  otpStore.delete(phone);

  let user = findUserByPhone(phone);
  if (!user) {
    // Auto-register as Customer only — OTP can never create Seller/Admin
    user = {
      id: generateId(),
      full_name: "New User",
      email: `${phone.replace("+", "")}@phone.placeholder`,
      password: null,
      role: "customer",
      is_verified: true, // phone verified via OTP itself
      seller_approved: null,
      business_name: null,
      phone,
      created_at: new Date().toISOString(),
    };
    mockUsers.push(user);
  }

  return buildAuthResponse(user);
}

// =====================================================================
// 5. Google OAuth — code exchange (mock)
// =====================================================================

export async function googleExchange({ code }) {
  await delay();

  if (!code || code === "invalid") {
    throw new ApiError(400, { message: "Invalid or expired authorization code" });
  }

  // Mock: derive a fake Google profile from the code so you can test
  // both "new user" and "existing user auto-link" paths.
  const mockGoogleEmail = `${code}@gmail.mock`;
  let user = findUserByEmail(mockGoogleEmail);

  if (!user) {
    user = {
      id: generateId(),
      full_name: "Google User",
      email: mockGoogleEmail,
      password: null,
      role: "customer",
      is_verified: true, // Google already verified the email
      seller_approved: null,
      business_name: null,
      phone: null,
      created_at: new Date().toISOString(),
    };
    mockUsers.push(user);
  }
  // If user existed already (e.g. registered via password with same email),
  // we auto-link — no changes needed, just issue tokens for that account.

  return buildAuthResponse(user);
}

// =====================================================================
// 6. Refresh (single-use rotation)
// =====================================================================

export async function refresh({ refresh_token }) {
  await delay(200);

  const entry = refreshTokenStore.get(refresh_token);
  if (!entry || entry.used) {
    throw new ApiError(401, { message: "Refresh token invalid, expired, or already used" });
  }

  entry.used = true; // rotation — old token can never be reused

  const user = mockUsers.find((u) => u.id === entry.userId);
  if (!user) throw new ApiError(401, { message: "User not found" });

  return issueTokenPair(user);
}

// =====================================================================
// 7. Logout
// =====================================================================

export async function logout({ refresh_token }) {
  await delay(200);
  refreshTokenStore.delete(refresh_token);
  return null; // 204 No Content
}

// =====================================================================
// 8. Get current user (session restore)
// =====================================================================

export async function getMe({ access_token }) {
  await delay(200);
  const user = getUserFromAccessToken(access_token);
  return sanitizeUser(user);
}

// =====================================================================
// 9 & 10. Admin — pending sellers list + approve/reject
// =====================================================================

export async function adminListPendingSellers({ access_token }) {
  await delay();
  requireAdmin(access_token);

  const pending = mockUsers.filter((u) => u.role === "seller" && u.seller_approved === false);

  return {
    sellers: pending.map((u) => ({
      id: u.id,
      full_name: u.full_name,
      email: u.email,
      business_name: u.business_name,
      created_at: u.created_at,
    })),
    total: pending.length,
  };
}

export async function adminApproveSeller({ access_token, seller_id }) {
  await delay();
  requireAdmin(access_token);

  const seller = mockUsers.find((u) => u.id === seller_id && u.role === "seller");
  if (!seller) throw new ApiError(404, { message: "Seller not found" });
  if (seller.seller_approved) throw new ApiError(409, { message: "Already approved" });

  seller.seller_approved = true;
  console.info(`[MOCK EMAIL] Approval email sent to ${seller.email}`);

  return { message: "Seller approved", seller_id };
}

export async function adminRejectSeller({ access_token, seller_id, reason }) {
  await delay();
  requireAdmin(access_token);

  const seller = mockUsers.find((u) => u.id === seller_id && u.role === "seller");
  if (!seller) throw new ApiError(404, { message: "Seller not found" });

  mockUsers = mockUsers.filter((u) => u.id !== seller_id);
  console.info(`[MOCK EMAIL] Rejection email sent to ${seller.email}. Reason: ${reason || "none given"}`);

  return { message: "Seller rejected", seller_id };
}

export { ApiError };