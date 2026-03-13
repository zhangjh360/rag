from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from app.database import get_db
from app.models.settings import Settings
from app.config.logging_config import get_app_logger
import json
from datetime import datetime
from typing import Dict, Any

router = APIRouter()
logger = get_app_logger()

@router.get("/settings")
async def get_all_settings(db: Session = Depends(get_db)):
    """获取所有设置"""
    try:
        settings_list = db.execute(select(Settings)).scalars().all()

        settings_dict = {
            'llm': {},
            'rag': {},
            'system': {}
        }

        for setting in settings_list:
            if setting.setting_type in settings_dict:
                try:
                    # 尝试解析JSON值
                    settings_dict[setting.setting_type][setting.setting_key] = json.loads(setting.setting_value)
                except json.JSONDecodeError:
                    # 如果不是JSON，直接存储字符串
                    settings_dict[setting.setting_type][setting.setting_key] = setting.setting_value

        return settings_dict

    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        raise HTTPException(status_code=500, detail="Failed to get settings")

@router.get("/settings/{setting_type}")
async def get_settings_by_type(setting_type: str, db: Session = Depends(get_db)):
    """根据类型获取设置"""
    try:
        if setting_type not in ['llm', 'rag', 'system']:
            raise HTTPException(status_code=400, detail="Invalid setting type")

        settings_list = db.execute(
            select(Settings).where(Settings.setting_type == setting_type)
        ).scalars().all()

        settings_dict = {}
        for setting in settings_list:
            try:
                settings_dict[setting.setting_key] = json.loads(setting.setting_value)
            except json.JSONDecodeError:
                settings_dict[setting.setting_key] = setting.setting_value

        return settings_dict

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting {setting_type} settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get {setting_type} settings")

@router.put("/settings/{setting_type}")
async def update_settings_by_type(setting_type: str, settings: Dict[str, Any], db: Session = Depends(get_db)):
    """根据类型更新设置"""
    try:
        if setting_type not in ['llm', 'rag', 'system']:
            raise HTTPException(status_code=400, detail="Invalid setting type")

        # 删除现有设置
        db.execute(
            delete(Settings).where(Settings.setting_type == setting_type)
        )

        # 插入新设置
        now = datetime.now().isoformat()
        for key, value in settings.items():
            setting = Settings(
                setting_type=setting_type,
                setting_key=key,
                setting_value=json.dumps(value, ensure_ascii=False),
                description=f"{setting_type} {key} setting",
                created_at=now,
                updated_at=now
            )
            db.add(setting)

        db.commit()

        return {"message": f"{setting_type} settings updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating {setting_type} settings: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update {setting_type} settings")

@router.get("/settings/{setting_type}/{key}")
async def get_single_setting(setting_type: str, key: str, db: Session = Depends(get_db)):
    """获取单个设置"""
    try:
        setting = db.execute(
            select(Settings).where(
                Settings.setting_type == setting_type,
                Settings.setting_key == key
            )
        ).scalar_one_or_none()

        if not setting:
            raise HTTPException(status_code=404, detail="Setting not found")

        try:
            value = json.loads(setting.setting_value)
        except json.JSONDecodeError:
            value = setting.setting_value

        return {
            "type": setting_type,
            "key": key,
            "value": value,
            "description": setting.description
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting setting {setting_type}.{key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get setting")

@router.put("/settings/{setting_type}/{key}")
async def update_single_setting(setting_type: str, key: str, data: Dict[str, Any], db: Session = Depends(get_db)):
    """更新单个设置"""
    try:
        if setting_type not in ['llm', 'rag', 'system']:
            raise HTTPException(status_code=400, detail="Invalid setting type")

        value = data.get('value')

        # 检查设置是否存在
        existing_setting = db.execute(
            select(Settings).where(
                Settings.setting_type == setting_type,
                Settings.setting_key == key
            )
        ).scalar_one_or_none()

        now = datetime.now().isoformat()

        if existing_setting:
            # 更新现有设置
            existing_setting.setting_value = json.dumps(value, ensure_ascii=False)
            existing_setting.updated_at = now
        else:
            # 创建新设置
            setting = Settings(
                setting_type=setting_type,
                setting_key=key,
                setting_value=json.dumps(value, ensure_ascii=False),
                description=f"{setting_type} {key} setting",
                created_at=now,
                updated_at=now
            )
            db.add(setting)

        db.commit()

        return {"message": f"Setting {setting_type}.{key} updated successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating setting {setting_type}.{key}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update setting")

@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """系统健康检查接口"""
    try:
        # 检查数据库连接
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = "error"
        logger.error(f"Database health check failed: {e}")

    # 获取系统信息
    from datetime import datetime
    import time

    start_time = time.time()

    return {
        "status": "healthy" if db_status == "ok" else "unhealthy",
        "timestamp": datetime.now().isoformat(),
        "database": db_status,
        "version": "1.0.0"
    }
