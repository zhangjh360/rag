from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_
from app.database import get_db
from app.models.llm_models import LLMGroup, LLMModel, LLMScenario
from app.config.logging_config import get_app_logger
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

router = APIRouter()
logger = get_app_logger()

# ==================== 模型分组管理 ====================

@router.get("/llm/groups", response_model=List[Dict])
async def get_all_groups(db: Session = Depends(get_db)):
    """获取所有模型分组"""
    try:
        groups = db.execute(select(LLMGroup).where(LLMGroup.is_active == True).order_by(LLMGroup.sort_order)).scalars().all()
        return [group.to_dict() if hasattr(group, 'to_dict') else {
            'id': group.id,
            'name': group.name,
            'display_name': group.display_name,
            'description': group.description,
            'sort_order': group.sort_order,
            'is_active': group.is_active
        } for group in groups]
    except Exception as e:
        logger.error(f"Error getting groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to get groups")

@router.post("/llm/groups")
async def create_group(group_data: Dict[str, Any], db: Session = Depends(get_db)):
    """创建新的模型分组"""
    try:
        now = datetime.now().isoformat()
        group = LLMGroup(
            name=group_data['name'],
            display_name=group_data['display_name'],
            description=group_data.get('description', ''),
            sort_order=group_data.get('sort_order', 0),
            is_active=True,
            created_at=now,
            updated_at=now
        )
        db.add(group)
        db.commit()
        db.refresh(group)

        return {
            "message": "Group created successfully",
            "group": {
                'id': group.id,
                'name': group.name,
                'display_name': group.display_name
            }
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create group")

@router.put("/llm/groups/{group_id}")
async def update_group(group_id: int, group_data: Dict[str, Any], db: Session = Depends(get_db)):
    """更新模型分组"""
    try:
        group = db.execute(select(LLMGroup).where(LLMGroup.id == group_id)).scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        group.display_name = group_data.get('display_name', group.display_name)
        group.description = group_data.get('description', group.description)
        group.sort_order = group_data.get('sort_order', group.sort_order)
        group.updated_at = datetime.now().isoformat()

        db.commit()

        return {"message": "Group updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating group: {e}")
        raise HTTPException(status_code=500, detail="Failed to update group")

@router.delete("/llm/groups/{group_id}")
async def delete_group(group_id: int, db: Session = Depends(get_db)):
    """删除模型分组"""
    try:
        group = db.execute(select(LLMGroup).where(LLMGroup.id == group_id)).scalar_one_or_none()
        if not group:
            raise HTTPException(status_code=404, detail="Group not found")

        # 检查是否有模型使用此分组
        models_count = db.execute(select(LLMModel).where(LLMModel.group_id == group_id)).scalars().all()
        if models_count:
            raise HTTPException(status_code=400, detail="Cannot delete group with existing models")

        db.delete(group)
        db.commit()

        return {"message": "Group deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting group: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete group")

# ==================== 模型管理 ====================

@router.get("/llm/models")
async def get_all_models(db: Session = Depends(get_db)):
    """获取所有LLM模型"""
    try:
        models = db.execute(select(LLMModel).order_by(LLMModel.group_id, LLMModel.name)).scalars().all()
        return [model.to_dict() for model in models]
    except Exception as e:
        logger.error(f"Error getting models: {e}")
        raise HTTPException(status_code=500, detail="Failed to get models")

@router.get("/llm/models/{model_id}")
async def get_model(model_id: int, db: Session = Depends(get_db)):
    """获取单个模型"""
    try:
        model = db.execute(select(LLMModel).where(LLMModel.id == model_id)).scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        return model.to_dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model: {e}")
        raise HTTPException(status_code=500, detail="Failed to get model")

@router.post("/llm/models")
async def create_model(model_data: Dict[str, Any], db: Session = Depends(get_db)):
    """创建新的LLM模型"""
    try:
        now = datetime.now().isoformat()
        model = LLMModel(
            name=model_data['name'],
            display_name=model_data['display_name'],
            provider=model_data['provider'],
            model_name=model_data['model_name'],
            api_key=model_data.get('api_key', ''),
            base_url=model_data.get('base_url', ''),
            group_id=model_data.get('group_id'),
            is_default=model_data.get('is_default', False),
            is_active=model_data.get('is_active', True),
            temperature=model_data.get('temperature', 0.7),
            max_tokens=model_data.get('max_tokens', 2000),
            top_p=model_data.get('top_p', 1.0),
            created_at=now,
            updated_at=now
        )
        db.add(model)
        db.commit()
        db.refresh(model)

        return {
            "message": "Model created successfully",
            "model": model.to_dict()
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating model: {e}")
        raise HTTPException(status_code=500, detail="Failed to create model")

@router.put("/llm/models/{model_id}")
async def update_model(model_id: int, model_data: Dict[str, Any], db: Session = Depends(get_db)):
    """更新LLM模型"""
    try:
        model = db.execute(select(LLMModel).where(LLMModel.id == model_id)).scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # 更新字段
        for key, value in model_data.items():
            if hasattr(model, key) and key not in ['id', 'created_at']:
                setattr(model, key, value)

        model.updated_at = datetime.now().isoformat()

        db.commit()

        return {"message": "Model updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating model: {e}")
        raise HTTPException(status_code=500, detail="Failed to update model")

@router.delete("/llm/models/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db)):
    """删除LLM模型"""
    try:
        model = db.execute(select(LLMModel).where(LLMModel.id == model_id)).scalar_one_or_none()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")

        # 检查是否被场景使用
        scenarios = db.execute(select(LLMScenario).where(LLMScenario.default_model_id == model_id)).scalars().all()
        if scenarios:
            raise HTTPException(status_code=400, detail="Cannot delete model used by scenarios")

        db.delete(model)
        db.commit()

        return {"message": "Model deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting model: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete model")

# ==================== 场景管理 ====================

@router.get("/llm/scenarios", response_model=List[Dict])
async def get_all_scenarios(db: Session = Depends(get_db)):
    """获取所有场景配置"""
    try:
        scenarios = db.execute(select(LLMScenario).order_by(LLMScenario.name)).scalars().all()
        return [scenario.to_dict() for scenario in scenarios]
    except Exception as e:
        logger.error(f"Error getting scenarios: {e}")
        raise HTTPException(status_code=500, detail="Failed to get scenarios")

@router.post("/llm/scenarios")
async def create_scenario(scenario_data: Dict[str, Any], db: Session = Depends(get_db)):
    """创建新场景"""
    try:
        now = datetime.now().isoformat()
        scenario = LLMScenario(
            name=scenario_data['name'],
            display_name=scenario_data['display_name'],
            description=scenario_data.get('description', ''),
            default_model_id=scenario_data.get('default_model_id'),
            is_active=scenario_data.get('is_active', True),
            created_at=now,
            updated_at=now
        )
        db.add(scenario)
        db.commit()
        db.refresh(scenario)

        return {
            "message": "Scenario created successfully",
            "scenario": scenario.to_dict()
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating scenario: {e}")
        raise HTTPException(status_code=500, detail="Failed to create scenario")

@router.put("/llm/scenarios/{scenario_id}")
async def update_scenario(scenario_id: int, scenario_data: Dict[str, Any], db: Session = Depends(get_db)):
    """更新场景"""
    try:
        scenario = db.execute(select(LLMScenario).where(LLMScenario.id == scenario_id)).scalar_one_or_none()
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

        for key, value in scenario_data.items():
            if hasattr(scenario, key) and key not in ['id', 'created_at']:
                setattr(scenario, key, value)

        scenario.updated_at = datetime.now().isoformat()

        db.commit()

        return {"message": "Scenario updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating scenario: {e}")
        raise HTTPException(status_code=500, detail="Failed to update scenario")

@router.delete("/llm/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    """删除场景"""
    try:
        scenario = db.execute(select(LLMScenario).where(LLMScenario.id == scenario_id)).scalar_one_or_none()
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")

        db.delete(scenario)
        db.commit()

        return {"message": "Scenario deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting scenario: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete scenario")

# ==================== 统一配置接口 ====================

@router.get("/llm/config")
async def get_llm_config(db: Session = Depends(get_db)):
    """获取完整的LLM配置"""
    try:
        # 获取分组
        groups = db.execute(select(LLMGroup).where(LLMGroup.is_active == True).order_by(LLMGroup.sort_order)).scalars().all()

        # 获取模型
        models = db.execute(select(LLMModel).order_by(LLMModel.group_id, LLMModel.name)).scalars().all()

        # 获取场景
        scenarios = db.execute(select(LLMScenario).order_by(LLMScenario.name)).scalars().all()

        # 组合数据
        result = {
            "groups": [group.to_dict() if hasattr(group, 'to_dict') else {
                'id': group.id,
                'name': group.name,
                'display_name': group.display_name,
                'description': group.description
            } for group in groups],
            "models": [model.to_dict() for model in models],
            "scenarios": [scenario.to_dict() for scenario in scenarios]
        }

        return result
    except Exception as e:
        logger.error(f"Error getting LLM config: {e}")
        raise HTTPException(status_code=500, detail="Failed to get LLM config")
