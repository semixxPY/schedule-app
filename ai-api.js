// 简化版 ai-api.js - 现在主要通过后端调用AI
window.aiService = {
    async generateReply(message, context) {
        try {
            const token = localStorage.getItem('userToken');
            const response = await fetch(
                'https://schedule-app-production-8f26.up.railway.app/api/ai/chat?message=' + encodeURIComponent(message),
                {
                    method: 'POST',
                    headers: token ? { 'Authorization': `Bearer ${token}` } : {}
                }
            );
            const data = await response.json();
            return data.reply;
        } catch (e) {
            return 'AI服务暂时不可用，请检查后端是否运行。';
        }
    }
};