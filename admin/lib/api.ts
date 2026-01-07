const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  if (authToken) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(error.detail || 'Request failed');
  }

  return response.json();
}

// Auth
export async function login(firebaseToken: string) {
  return fetchAPI('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ firebase_token: firebaseToken }),
  });
}

export async function getMe() {
  return fetchAPI('/auth/me');
}

// Dashboard
export async function getDashboardStats() {
  return fetchAPI('/admin/dashboard/stats');
}

// Users
export async function getFounders(params?: { search?: string; limit?: number; offset?: number }) {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set('search', params.search);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return fetchAPI(`/admin/users/founders${query ? `?${query}` : ''}`);
}

export async function getInvestors(params?: { search?: string; limit?: number; offset?: number }) {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set('search', params.search);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return fetchAPI(`/admin/users/investors${query ? `?${query}` : ''}`);
}

export async function getTalent(params?: { search?: string; status?: string; limit?: number; offset?: number }) {
  const searchParams = new URLSearchParams();
  if (params?.search) searchParams.set('search', params.search);
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return fetchAPI(`/admin/users/talent${query ? `?${query}` : ''}`);
}

export async function approveTalent(profileId: string) {
  return fetchAPI(`/admin/talent/${profileId}/approve`, { method: 'POST' });
}

export async function rejectTalent(profileId: string, reason?: string) {
  return fetchAPI(`/admin/talent/${profileId}/reject`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function getTalentStats() {
  return fetchAPI('/admin/talent/stats');
}

// Support Tickets
export async function getSupportTickets(params?: { status?: string; limit?: number; offset?: number }) {
  const searchParams = new URLSearchParams();
  if (params?.status) searchParams.set('status', params.status);
  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());

  const query = searchParams.toString();
  return fetchAPI(`/admin/support/tickets${query ? `?${query}` : ''}`);
}

export async function getSupportTicket(ticketId: string) {
  return fetchAPI(`/admin/support/tickets/${ticketId}`);
}

export async function replyToTicket(ticketId: string, content: string) {
  return fetchAPI(`/admin/support/tickets/${ticketId}/reply`, {
    method: 'POST',
    body: JSON.stringify({ content }),
  });
}

export async function resolveTicket(ticketId: string) {
  return fetchAPI(`/admin/support/tickets/${ticketId}/resolve`, { method: 'POST' });
}

export async function reopenTicket(ticketId: string) {
  return fetchAPI(`/admin/support/tickets/${ticketId}/reopen`, { method: 'POST' });
}
