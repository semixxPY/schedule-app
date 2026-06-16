// 简化版 ai-api.js - 现在主要通过后端调用AI
window.aiService = {
    async generateReply(message, context) {
        // 现在主要通过后端 /api/ai/chat 接口调用AI
        try {
            const response = await fetch(
                'https://schedule-app-production-8f26.up.railway.app/api/ai/chat?message=' + encodeURIComponent(message),
                { method: 'POST' }
            );
            const data = await response.json();
            return data.reply;
        } catch (e) {
            return 'AI服务暂时不可用，请检查后端是否运行。';
        }
    }
};