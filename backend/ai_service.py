import json
import requests

class AIService:
    def __init__(self, api_key: str = "", model: str = "doubao-pro"):
        self.api_key = api_key
        self.model = model
        # 豆包的API地址
        self.base_url = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
    
    # 生成作息计划（支持用户自定义偏好）
    def generate_plan(self, activities: list, target_date: str, user_preference: str = ""):
        activity_text = "\n".join([
            f"- {act.get('date', '')} {act.get('start_time', '')}-{act.get('end_time', '')} {act.get('title', '')} ({act.get('type', '')})"
            for act in activities
        ])
        preference_text = f"\n\n【用户的特殊要求（必须遵守！）】\n{user_preference}" if user_preference else ""
        messages = [
            {"role": "system", "content": 
            """你是一个专业的作息安排助手，擅长分析用户作息并提供建议。
            【重要规则】
            1. 你只需要基于用户提供的"最近7天活动记录"来分析和生成计划
            2. 不要编造或想象没有提到的活动数据
            3. 如果用户活动记录较少，按照健康作息的标准建议来安排
            4. 如果用户的作息偏离健康作息过多，将计划向健康作息方向调整，但不要完全颠覆用户习惯
            5. 必须严格以JSON数组格式返回，不要其他解释文字"""},
                        {"role": "user", "content": f"""
            用户最近7天的活动记录（共 {len(activities)} 条）:
            {activity_text}

            请根据以上实际活动，为 {target_date} 生成一份合理的作息计划。
            {preference_text}
            【要求】
            1. 参考用户过去的作息节奏，生成符合用户习惯的安排
            2. 总共有 6-10 个活动
            3. 只返回 JSON 数组，不要其他文字
            4. 对用户不健康作息的部分适当调整，差距不能超过 2 小时

            【每个活动的JSON字段】
            - start_time: HH:mm （24小时制，如 09:00
            - end_time: HH:mm （24小时制，如 12:00
            - title: 活动名称（简短描述
            - type: 类型，只能是下面4个中的一个
                【学习/工作、休息、运动/娱乐、通勤/家务/吃饭】

            【返回格式示例】
            [
            {{"start_time": "07:00", "end_time": "08:00", "title": "起床活动", "type": "通勤/家务/吃饭"}},
            {{"start_time": "09:00", "end_time": "12:00", "title": "工作/学习", "type": "学习/工作"}}
            ]

            【再次提醒】只返回JSON数组，绝对不要加任何其他解释！"""}
        ]
        print("\n" + "="*60)
        print("📝 发送给AI的完整提示词（generate_plan）:")
        print("="*60)
        for msg in messages:
            print(f"\n【{msg['role'].upper()}】")
            print(msg['content'])
        print("\n" + "="*60 + "\n")
        
        return self._call_api(messages)
    
    # 与用户聊天对话
    def chat(self, user_message: str, today_activities: list):
        activity_text = "\n".join([
            f"- {act.get('start_time', '')}-{act.get('end_time', '')} {act.get('title', '')} ({act.get('type', '')})"
            for act in today_activities
        ]) if today_activities else "暂无记录"
        
        messages = [
            {"role": "system", "content": f"""你是一个友好的作息安排助手。
            用户今天的活动记录：
            {activity_text}

            请用中文回答用户问题，帮助用户优化作息安排。注意：
            1.回答要简洁友好，不要太长。
            2.不要简单重复用户的日程
            3.将用户作息与健康作息比对，如果偏离过多，适当给出建议"""},
            {"role": "user", "content": user_message}
        ]
        
        return self._call_api(messages)
    
    # 通用调用API
    def _call_api(self, messages: list):
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            result = response.json()
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                return f"AI返回数据异常：{json.dumps(result, ensure_ascii=False)}"
        except Exception as e:
            return f"AI调用失败：{str(e)}"


# 简单测试
if __name__ == "__main__":
    print("AI服务模块已就绪...")
    print("可以通过 main.py 来调用这个服务")