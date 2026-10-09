const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api";

async function request(path, { method = "GET", body, token } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });

  let data = null;
  try {
    data = await res.json();
  } catch {
    // no body
  }

  if (!res.ok) {
    const message = data?.detail || `Request failed (${res.status})`;
    throw new Error(message);
  }
  return data;
}

export const api = {
  // Products
  listCategories: () => request("/products/categories"),
  searchProducts: (params = {}) => {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null && v !== "")
    ).toString();
    return request(`/products${qs ? `?${qs}` : ""}`);
  },
  getProduct: (id) => request(`/products/${id}`),

  // Cart
  getCart: (sessionId) => request(`/cart/${sessionId}`),
  addToCart: (sessionId, variantId, quantity) =>
    request("/cart/add", { method: "POST", body: { session_id: sessionId, variant_id: variantId, quantity } }),
  updateCartItem: (sessionId, variantId, quantity) =>
    request(`/cart/${sessionId}/items/${variantId}`, { method: "PUT", body: { session_id: sessionId, quantity } }),
  removeCartItem: (sessionId, variantId) =>
    request(`/cart/${sessionId}/items/${variantId}`, { method: "DELETE" }),

  // Orders
  createOrder: (payload) => request("/orders", { method: "POST", body: payload }),
  getOrder: (orderNumber) => request(`/orders/${orderNumber}`),
  getCustomerOrders: (phone) => request(`/orders?phone=${encodeURIComponent(phone)}`),
  cancelOrder: (orderNumber) => request(`/orders/${orderNumber}/cancel`, { method: "POST" }),

  // Chat
  sendChatMessage: (sessionId, message, customerName) =>
    request("/chat", { method: "POST", body: { session_id: sessionId, message, customer_name: customerName } }),

  // Admin
  adminLogin: (username, password) => request("/admin/login", { method: "POST", body: { username, password } }),
  adminDashboard: (token) => request("/admin/dashboard", { token }),
  adminListProducts: (token) => request("/admin/products", { token }),
  adminCreateProduct: (token, payload) => request("/admin/products", { method: "POST", body: payload, token }),
  adminUpdateProduct: (token, id, payload) => request(`/admin/products/${id}`, { method: "PUT", body: payload, token }),
  adminDeleteProduct: (token, id) => request(`/admin/products/${id}`, { method: "DELETE", token }),
  adminAddVariant: (token, productId, payload) =>
    request(`/admin/products/${productId}/variants`, { method: "POST", body: payload, token }),
  adminUpdateVariant: (token, variantId, payload) =>
    request(`/admin/variants/${variantId}`, { method: "PUT", body: payload, token }),
  adminListOrders: (token, status) => request(`/admin/orders${status ? `?status=${status}` : ""}`, { token }),
  adminUpdateOrderStatus: (token, orderId, payload) =>
    request(`/admin/orders/${orderId}/status`, { method: "PUT", body: payload, token }),
  adminAiChat: (token, message) => request("/admin/ai-chat", { method: "POST", body: { message }, token }),
  adminFulfillmentEvents: (token, limit = 15) => request(`/admin/fulfillment-events?limit=${limit}`, { token }),
  adminListAILogs: (token, limit = 50) => request(`/admin/ai-logs?limit=${limit}`, { token }),
  adminCreateCategory: (token, name) => request("/admin/categories", { method: "POST", body: { name, slug: name.toLowerCase().replace(/\s+/g, "-") }, token }),
};

export { BASE_URL };
