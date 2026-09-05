import axios from "axios";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
  withCredentials: true,
});

/**
 * Pulls a human-readable message out of an API error response body.
 * Different endpoints shape their errors differently:
 *   - a single string body
 *   - { detail: "..." } / { error: "..." } / { message: "..." }
 *   - DRF serializer validation errors: { field: ["msg", ...], ... }
 * (register/login previously only checked for `detail`/`error`, so a
 * plain-string `message` from LoginView, or field-level validation
 * errors from RegisterView, silently fell through to a generic
 * fallback instead of reaching the user.) Returns `fallback` if nothing
 * usable is found.
 */
export function extractErrorMessage(data: unknown, fallback: string): string {
  if (!data) {
    return fallback;
  }

  if (typeof data === "string") {
    return data;
  }

  if (typeof data === "object") {
    const obj = data as Record<string, unknown>;

    if (typeof obj.detail === "string") return obj.detail;
    if (typeof obj.error === "string") return obj.error;
    if (typeof obj.message === "string") return obj.message;

    // DRF validation errors look like { field: ["msg1", "msg2"], ... } -
    // flatten every field's messages into one readable string.
    const messages = Object.values(obj)
      .flat()
      .filter((value): value is string => typeof value === "string");

    if (messages.length > 0) {
      return messages.join(" ");
    }
  }

  return fallback;
}

let isRefreshing = false;

let refreshSubscribers: (() => void)[] = [];

function subscribeTokenRefresh(callback: () => void) {
  refreshSubscribers.push(callback);
}

function onRefreshFinished() {
  refreshSubscribers.forEach((callback) => callback());
  refreshSubscribers = [];
}

api.interceptors.response.use(
  (response) => {
    return response;
  },

  async (error) => {
    const originalRequest = error.config;

    // A 401 from these endpoints means "wrong credentials" or "no/invalid
    // refresh token" - not "an authenticated request's access token
    // expired mid-session". Treating it as the latter (as the code below
    // does for every other 401) tried to "refresh" a session that never
    // existed, which itself 401'd, and then force-reloaded the page via
    // window.location.href - wiping out the login/signup form's error
    // state before it could ever be shown, and leaving the submit button
    // stuck mid-request. Let these reject normally so the calling page
    // can read and display the real error.
    const isAuthEndpoint =
      typeof originalRequest?.url === "string" &&
      (originalRequest.url.includes("/api/auth/login/") ||
        originalRequest.url.includes("/api/auth/register/") ||
        originalRequest.url.includes("/api/auth/refresh/"));

    // Only handle 401 once, and never for the auth endpoints themselves
    if (
      isAuthEndpoint ||
      error.response?.status !== 401 ||
      originalRequest._retry
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    // If another request is already refreshing,
    // wait for it to finish.
    if (isRefreshing) {
      return new Promise((resolve) => {
        subscribeTokenRefresh(() => {
          resolve(api(originalRequest));
        });
      });
    }

    isRefreshing = true;

    try {
      // Browser automatically sends the
      // HttpOnly refresh_token cookie.
      await api.post("/api/auth/refresh/");

      isRefreshing = false;

      // Retry requests waiting for refresh
      onRefreshFinished();

      // Retry original request
      return api(originalRequest);

    } catch (refreshError) {
      isRefreshing = false;
      refreshSubscribers = [];

      // Refresh token is also invalid/expired
      window.location.href = "/login";

      return Promise.reject(refreshError);
    }
  }
);

export default api;