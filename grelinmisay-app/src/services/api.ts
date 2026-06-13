const API_BASE = '/api';

interface RequestOptions {
  method?: string;
  body?: any;
  token?: string;
}

export async function request<T = any>(url: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, token } = options;
  const headers: Record<string, string> = { 'Content-Type': 'application/json' };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const res = await fetch(`${API_BASE}${url}`, {
    method,
    headers,
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (data.code !== 0) {
    throw new Error(data.message || '请求失败');
  }
  return data.data;
}

// 认证
export const authAPI = {
  sendCode: (phone: string) => request('/auth/send_code', { method: 'POST', body: { phone } }),
  register: (phone: string, password: string, nickname: string) =>
    request('/auth/register', { method: 'POST', body: { phone, password, nickname } }),
  login: (phone: string, password: string) =>
    request('/auth/login', { method: 'POST', body: { phone, password } }),
};

// 用户
export const userAPI = {
  getMe: (token: string) => request('/users/me', { token }),
  updateMe: (token: string, data: any) => request('/users/me', { method: 'PUT', body: data, token }),
};

// 目标
export const goalAPI = {
  list: (token: string) => request('/goals', { token }),
  create: (token: string, data: any) => request('/goals', { method: 'POST', body: data, token }),
  update: (token: string, id: string, data: any) => request(`/goals/${id}`, { method: 'PUT', body: data, token }),
  delete: (token: string, id: string) => request(`/goals/${id}`, { method: 'DELETE', token }),
  checkin: (token: string, id: string) => request(`/goals/${id}/checkin`, { method: 'POST', token }),
};

// 训练
export const trainingAPI = {
  actions: () => request<{ actions: Record<string, string[]> }>('/training/actions'),
  records: (token: string) => request('/training/records', { token }),
  create: (token: string, data: any) => request('/training/records', { method: 'POST', body: data, token }),
};

// 日历
export const calendarAPI = {
  events: (token: string, start: string, end: string) =>
    request(`/calendar/events?start_date=${start}&end_date=${end}`, { token }),
};

// AI
export const aiAPI = {
  chat: (token: string, message: string) =>
    request('/ai/chat', { method: 'POST', body: { message }, token }),
};