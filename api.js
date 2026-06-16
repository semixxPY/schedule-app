const API_BASE_URL = 'https://schedule-app-production-8f26.up.railway.app';

// 从 localStorage 获取 token
function getAuthToken() {
    return localStorage.getItem('userToken');
}

// 获取当前用户信息
function getCurrentUser() {
    const userData = localStorage.getItem('currentUser');
    return userData ? JSON.parse(userData) : null;
}

// 封装HTTP请求（自动携带认证信息）
const api = {
    async get(url) {
        const headers = { 'Content-Type': 'application/json' };
        const token = getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE_URL}${url}`, {
            method: 'GET',
            headers: headers
        });
        return await handleResponse(response);
    },

    async post(url, data) {
        const headers = { 'Content-Type': 'application/json' };
        const token = getAuthToken();
        if (token && !url.includes('/auth/')) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE_URL}${url}`, {
            method: 'POST',
            headers: headers,
            body: JSON.stringify(data)
        });
        return await handleResponse(response);
    },

    async put(url, data) {
        const headers = { 'Content-Type': 'application/json' };
        const token = getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE_URL}${url}`, {
            method: 'PUT',
            headers: headers,
            body: JSON.stringify(data)
        });
        return await handleResponse(response);
    },

    async delete(url) {
        const headers = { 'Content-Type': 'application/json' };
        const token = getAuthToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }
        
        const response = await fetch(`${API_BASE_URL}${url}`, {
            method: 'DELETE',
            headers: headers
        });
        return await handleResponse(response);
    }
};

async function handleResponse(response) {
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.detail || data.message || '请求失败');
    }
    return data;
}

// 用户认证相关 API
window.authAPI = {
    // 注册
    async register(username, password) {
        const data = await api.post('/api/auth/register', { username, password });
        // 保存 token 和用户信息
        localStorage.setItem('userToken', data.token);
        localStorage.setItem('currentUser', JSON.stringify({ id: data.user_id, username: data.username }));
        return data;
    },
    
    // 登录
    async login(username, password) {
        const data = await api.post('/api/auth/login', { username, password });
        localStorage.setItem('userToken', data.token);
        localStorage.setItem('currentUser', JSON.stringify({ id: data.user_id, username: data.username }));
        return data;
    },
    
    // 退出登录
    logout() {
        localStorage.removeItem('userToken');
        localStorage.removeItem('currentUser');
        localStorage.removeItem('activities');
        localStorage.removeItem('userSettings');
    },
    
    // 检查是否已登录
    isLoggedIn() {
        return !!getAuthToken();
    },
    
    // 获取当前用户
    getCurrentUser: getCurrentUser
};

// 活动相关 API
window.activityAPI = {
    async getAll() { return await api.get('/api/activities'); },
    async getById(id) { return await api.get(`/api/activities/${id}`); },
    async create(activity) { return await api.post('/api/activities', activity); },
    async update(id, activity) { return await api.put(`/api/activities/${id}`, activity); },
    async delete(id) { return await api.delete(`/api/activities/${id}`); },
    async getByDateRange(start, end) { return await api.get(`/api/activities/date-range?start=${start}&end=${end}`); }
};

// 用户设置相关 API
window.settingsAPI = {
    async get() { return await api.get('/api/settings'); },
    async update(settings) { return await api.put('/api/settings', settings); }
};