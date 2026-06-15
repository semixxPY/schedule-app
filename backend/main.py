from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json
import models
import schemas
from database import engine, get_db
# 导入AI服务
from ai_service import AIService
import json

# ===== 配置AI服务 =====
AI_API_KEY = "ark-0e6da7b4-9524-4d24-b1b6-27a7cc1412ad-1d7b2"
AI_MODEL = "doubao-seed-2-0-lite-260428"
ai_service = AIService(api_key=AI_API_KEY, model=AI_MODEL)
# 创建数据库表
models.Base.metadata.create_all(bind=engine)

# 创建FastAPI应用
app = FastAPI(title="作息安排记录 API", version="1.0.0")

# ==================== 活动相关接口 ====================

# 获取所有活动
@app.get("/api/activities", response_model=list[schemas.ActivityResponse])
def get_all_activities(db: Session = Depends(get_db)):
    return db.query(models.Activity).order_by(models.Activity.date, models.Activity.start_time).all()

# 获取单个活动
@app.get("/api/activities/{activity_id}", response_model=schemas.ActivityResponse)
def get_activity(activity_id: str, db: Session = Depends(get_db)):
    activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    return activity

# 创建活动
@app.post("/api/activities", response_model=schemas.ActivityResponse)
def create_activity(activity: schemas.ActivityCreate, db: Session = Depends(get_db)):
    # 检查是否已存在相同ID的活动
    existing = db.query(models.Activity).filter(models.Activity.id == activity.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="活动ID已存在")
    
    # 创建新活动
    db_activity = models.Activity(**activity.model_dump())
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    
    # 返回格式化后的响应
    print(f"创建活动: {db_activity.id}, created_at: {db_activity.created_at}, updated_at: {db_activity.updated_at}")
    return schemas.ActivityResponse.model_validate(db_activity)

# 更新活动
# ============ 更新活动（支持移动/复制时修改日期和时间）============
@app.put("/api/activities/{activity_id}", response_model=schemas.ActivityResponse)
def update_activity(activity_id: str, activity_update: schemas.ActivityUpdate, db: Session = Depends(get_db)):
    
    activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail=f"活动不存在: {activity_id}")
    
    # 只更新提供的字段（日期、时间、标题等）
    update_data = activity_update.model_dump(exclude_unset=True)
    
    for key, value in update_data.items():
        if hasattr(activity, key):
            setattr(activity, key, value)
    
    db.commit()
    db.refresh(activity)
    
    return schemas.ActivityResponse.model_validate(activity)
# 删除活动
@app.delete("/api/activities/{activity_id}")
def delete_activity(activity_id: str, db: Session = Depends(get_db)):
    activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    
    db.delete(activity)
    db.commit()
    return {"message": "活动删除成功"}

# 按日期范围查询活动
@app.get("/api/activities/date-range", response_model=list[schemas.ActivityResponse])
def get_activities_by_date_range(start_date: str, end_date: str, db: Session = Depends(get_db)):
    activities = db.query(models.Activity)\
        .filter(models.Activity.date >= start_date)\
        .filter(models.Activity.date <= end_date)\
        .order_by(models.Activity.date, models.Activity.start_time)\
        .all()
    return activities

# ==================== 用户设置相关接口 ====================

# 获取用户设置
@app.get("/api/settings", response_model=schemas.UserSettingsResponse)
def get_user_settings(db: Session = Depends(get_db)):
    settings = db.query(models.UserSettings).first()
    if not settings:
        # 如果没有设置，创建默认设置
        settings = models.UserSettings()
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

# 更新用户设置
@app.put("/api/settings", response_model=schemas.UserSettingsResponse)
def update_user_settings(settings_update: schemas.UserSettingsBase, db: Session = Depends(get_db)):
    settings = db.query(models.UserSettings).first()
    if not settings:
        # 如果没有设置，创建新设置
        settings = models.UserSettings(**settings_update.model_dump())
    else:
        # 更新现有设置
        update_data = settings_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(settings, key, value)
    
    db.commit()
    db.refresh(settings)
    return settings

# 健康检查接口
@app.get("/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
# ============ AI生成计划接口 ============

@app.post("/api/ai/generate-plan")
async def generate_ai_plan(db: Session = Depends(get_db)):
    from datetime import datetime, timedelta
    
    today = datetime.now()
    tomorrow = today + timedelta(days=1)
    tomorrow_str = tomorrow.strftime('%Y-%m-%d')
    
    # 获取过去一周的活动
    # 获取过去一周（精确7天）的活动数据
    week_ago = today - timedelta(days=7)
    week_ago_str = week_ago.strftime('%Y-%m-%d')
    today_str = today.strftime('%Y-%m-%d')
    
    week_activities = db.query(models.Activity).\
        filter(models.Activity.date >= week_ago_str).\
        filter(models.Activity.date <= today_str).\
        order_by(models.Activity.date, models.Activity.start_time).all()
    
    print(f"\n📊 日期范围: {week_ago_str} ~ {today_str}")
    print(f"📊 数据库中找到 {len(week_activities)} 条活动记录")
    
    if len(week_activities) == 0:
        raise HTTPException(status_code=400, detail="前一周没有活动数据，无法生成计划。请先记录一些活动！")
    
    # 转换为简单格式
    activities_data = [
        {
            "date": act.date,
            "start_time": act.start_time,
            "end_time": act.end_time,
            "title": act.title,
            "type": act.type
        }
        for act in week_activities
    ]
    
    print(f"\n=== AI开始生成计划 ===")
    print(f"目标日期: {tomorrow_str}")
    print(f"活动数据量: {len(activities_data)}条")
    
    try:
        # ========== 调用AI生成计划 ==========
        ai_response = ai_service.generate_plan(activities_data, tomorrow_str)
        print(f"AI返回内容:\n{ai_response}\n")
        
        # 尝试解析AI返回的JSON
        plan_activities = None
        try:
            # 找到第一个 [ 和最后一个 ]，截取中间部分
            start_idx = ai_response.find('[')
            end_idx = ai_response.rfind(']') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = ai_response[start_idx:end_idx]
                plan_activities = json.loads(json_str)
                print(f"✓ 成功解析为JSON，共 {len(plan_activities)} 个活动")
            else:
                print("✗ AI返回的不是JSON格式")
        except Exception as e:
            print(f"✗ JSON解析失败: {e}")
            plan_activities = None
        
        # 如果AI生成失败，使用规则生成
        if not plan_activities or len(plan_activities) == 0:
            print("使用规则生成作为后备方案")
            plan_activities = generate_plan_by_rules(tomorrow_str, activities_data)
        
        # 删除明天已存在的计划
        existing = db.query(models.Activity).\
            filter(models.Activity.date == tomorrow_str).\
            filter(models.Activity.is_plan == True).all()
        for plan in existing:
            db.delete(plan)
        db.commit()
        
        # 保存新计划到数据库
        saved = []
        for idx, plan in enumerate(plan_activities):
            # 校验type字段
            valid_types = ['学习/工作', '休息', '运动/娱乐', '通勤/家务/吃饭']
            activity_type = plan.get('type', '学习/工作')
            if activity_type not in valid_types:
                activity_type = '学习/工作'
            
            new_act = models.Activity(
                id=f"ai-{tomorrow_str}-{idx+1:02d}",
                title=plan.get('title', '活动'),
                type=activity_type,
                date=tomorrow_str,
                start_time=plan.get('start_time', '09:00'),
                end_time=plan.get('end_time', '10:00'),
                notes="AI生成计划",
                is_plan=True
            )
            db.add(new_act)
            saved.append(new_act)
        
        db.commit()
        print(f"✓ 计划已保存到数据库，共 {len(saved)} 个活动\n")
        
        return {
            "message": f"已成功生成明天({tomorrow_str})的计划",
            "date": tomorrow_str,
            "total_activities": len(saved),
            "activities": [
                {
                    "id": a.id,
                    "title": a.title,
                    "type": a.type,
                    "start_time": a.start_time,
                    "end_time": a.end_time
                }
                for a in saved
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"生成计划失败: {e}")
        raise HTTPException(status_code=500, detail=f"生成计划失败: {str(e)}")
    
# ============ AI聊天接口 ============
@app.post("/api/ai/chat")
async def ai_chat(message: str, db: Session = Depends(get_db)):
    from datetime import datetime
    today_str = datetime.now().strftime('%Y-%m-%d')
    
    # 获取今天的活动
    today_activities = db.query(models.Activity).\
        filter(models.Activity.date == today_str).\
        order_by(models.Activity.start_time).all()
    
    activities_data = [
        {
            "start_time": a.start_time,
            "end_time": a.end_time,
            "title": a.title,
            "type": a.type
        }
        for a in today_activities
    ]
    
    # 调用AI
    response = ai_service.chat(message, activities_data)
    
    return {"reply": response}

def generate_plan_by_rules(date_str, activity_summary):
    """
    基于规则生成智能计划（作为AI的后备方案）
    """
    import random
    
    # 分析用户习惯
    work_count = len(activity_summary.get('学习/工作', []))
    rest_count = len(activity_summary.get('休息', []))
    exercise_count = len(activity_summary.get('运动/娱乐', []))
    
    # 根据历史数据调整比例
    plans = []
    
    # 固定的基础作息
    base_schedule = [
        {'title': '起床、晨间活动', 'type': '通勤/家务/吃饭', 'start_time': '07:00', 'end_time': '07:30'},
        {'title': '早餐', 'type': '通勤/家务/吃饭', 'start_time': '07:30', 'end_time': '08:00'},
        {'title': '工作/学习时间', 'type': '学习/工作', 'start_time': '09:00', 'end_time': '12:00'},
        {'title': '午餐', 'type': '通勤/家务/吃饭', 'start_time': '12:00', 'end_time': '13:00'},
        {'title': '午休', 'type': '休息', 'start_time': '13:00', 'end_time': '14:00'},
        {'title': '下午工作/学习', 'type': '学习/工作', 'start_time': '14:00', 'end_time': '17:30'},
        {'title': '晚餐', 'type': '通勤/家务/吃饭', 'start_time': '17:30', 'end_time': '18:30'},
        {'title': '休闲/运动时间', 'type': '运动/娱乐', 'start_time': '18:30', 'end_time': '21:00'},
        {'title': '阅读/准备明天', 'type': '学习/工作', 'start_time': '21:00', 'end_time': '22:00'},
        {'title': '睡前准备', 'type': '休息', 'start_time': '22:00', 'end_time': '23:00'},
    ]
    
    # 根据用户历史习惯微调
    if exercise_count == 0:
        # 用户最近没怎么运动，增加提醒
        base_schedule[7]['notes'] = '建议今天增加运动，保持健康'
    
    if rest_count < work_count * 0.3:
        # 休息时间偏少
        base_schedule[5]['end_time'] = '17:00'
        base_schedule.insert(5, {'title': '短暂休息', 'type': '休息', 'start_time': '15:30', 'end_time': '16:00'})
    
    return base_schedule


# 聊天调整计划接口
@app.post("/api/ai/adjust-plan")
async def adjust_plan(
    message: str,
    target_date: str = None,
    db: Session = Depends(get_db)
):
    """
    根据用户的聊天消息调整计划
    """
    from datetime import datetime, timedelta
    
    if not target_date:
        tomorrow = datetime.now() + timedelta(days=1)
        target_date = tomorrow.strftime('%Y-%m-%d')
    
    # 获取当前计划
    current_plans = db.query(models.Activity)\
        .filter(models.Activity.date == target_date)\
        .filter(models.Activity.is_plan == True)\
        .order_by(models.Activity.start_time)\
        .all()
    
    if not current_plans:
        return {
            "message": f"{target_date}还没有计划，请先生成计划",
            "activities": []
        }
    
    # 简单的关键词匹配调整（实际可以接入AI）
    message_lower = message.lower()
    
    response_message = "已为您调整计划："
    adjusted = False
    
    # 删除运动时间
    if '不运动' in message or '取消运动' in message or '不要运动' in message:
        for act in current_plans:
            if '运动' in act.type or '运动' in act.title:
                db.delete(act)
                adjusted = True
        response_message = "已取消运动安排"
    
    # 增加学习时间
    elif '多学习' in message or '增加学习' in message:
        # 将休息时间改为学习
        for act in current_plans:
            if act.type == '休息' and '午休' not in act.title:
                act.type = '学习/工作'
                act.title = '额外学习时间'
                adjusted = True
        response_message = "已将部分休息时间改为学习时间"
    
    # 早睡
    elif '早睡' in message or '早点睡' in message:
        for act in current_plans:
            if act.start_time >= '22:00':
                act.end_time = '22:30' if act.start_time == '22:00' else act.end_time
                if '准备' in act.title:
                    act.end_time = '22:30'
                adjusted = True
        response_message = "已调整为早睡计划"
    
    # 睡懒觉/晚起
    elif '睡懒觉' in message or '晚起' in message or '明天晚点起' in message:
        for act in current_plans:
            if act.start_time <= '08:00':
                db.delete(act)
                adjusted = True
        # 添加新的起床时间
        new_activity = models.Activity(
            id=f"plan-{target_date}-lazy",
            title='睡懒觉~',
            type='休息',
            date=target_date,
            start_time='08:00',
            end_time='09:00',
            notes='根据用户调整',
            is_plan=True
        )
        db.add(new_activity)
        response_message = "已调整为晚起计划"
    
    db.commit()
    
    # 获取更新后的计划
    updated_plans = db.query(models.Activity)\
        .filter(models.Activity.date == target_date)\
        .filter(models.Activity.is_plan == True)\
        .order_by(models.Activity.start_time)\
        .all()
    
    return {
        "message": response_message if adjusted else "计划未变化，您可以说：'取消运动'、'多学习'、'早睡'、'晚起'等",
        "date": target_date,
        "adjusted": adjusted,
        "activities": [
            {
                "id": act.id,
                "title": act.title,
                "type": act.type,
                "date": act.date,
                "start_time": act.start_time,
                "end_time": act.end_time,
                "is_plan": act.is_plan
            }
            for act in updated_plans
        ]
    }


# ============ 辅助功能：导出数据 ============
@app.get("/api/activities/plans/{date}")
def get_plans_by_date(date: str, db: Session = Depends(get_db)):
    """获取指定日期的计划活动"""
    plans = db.query(models.Activity)\
        .filter(models.Activity.date == date)\
        .filter(models.Activity.is_plan == True)\
        .order_by(models.Activity.start_time)\
        .all()
    
    return {
        "date": date,
        "total": len(plans),
        "activities": [
            {
                "id": act.id,
                "title": act.title,
                "type": act.type,
                "start_time": act.start_time,
                "end_time": act.end_time,
                "notes": act.notes
            }
            for act in plans
        ]
    }
# ============ 确认计划接口（点击计划后把is_plan改为0）============
@app.put("/api/activities/{activity_id}/confirm")
def confirm_activity(activity_id: str, db: Session = Depends(get_db)):
    activity = db.query(models.Activity).filter(models.Activity.id == activity_id).first()
    
    if not activity:
        raise HTTPException(status_code=404, detail="活动不存在")
    
    activity.is_plan = False
    db.commit()
    
    print(f"✅ 已确认计划: {activity.title} ({activity.date} {activity.start_time}-{activity.end_time})")
    
    return {
        "message": "计划已确认",
        "id": activity.id,
        "title": activity.title,
        "is_plan": False
    }


# ============ 自动清理过期计划接口（加载页面时调用）============
@app.post("/api/ai/clean-expired-plans")
def clean_expired_plans(db: Session = Depends(get_db)):
    from datetime import datetime
    
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M')
    
    # print(f"\n🧹 清理过期计划...")
    # print(f"   当前日期: {today_str}, 当前时间: {current_time}")
    
    # 找出所有 is_plan=1 的活动
    plan_activities = db.query(models.Activity).filter(models.Activity.is_plan == True).all()
    
    deleted_count = 0
    for activity in plan_activities:
        # 如果活动日期 < 今天 → 删除
        # 如果活动日期 = 今天，且活动结束时间 < 当前时间 → 删除
        should_delete = False
        
        if activity.date < today_str:
            should_delete = True
            reason = "日期已过"
        elif activity.date == today_str and activity.end_time < current_time:
            should_delete = True
            reason = "时间已过"
        
        if should_delete:
            print(f"   删除: {activity.date} {activity.start_time}-{activity.end_time} {activity.title} ({reason})")
            db.delete(activity)
            deleted_count += 1
    
    if deleted_count > 0:
        db.commit()
    
    print(f"   共清理 {deleted_count} 个过期计划\n")
    
    return {
        "message": f"清理完成，共删除 {deleted_count} 个过期计划",
        "deleted_count": deleted_count
    }

# ============ 主程序入口 ============
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)