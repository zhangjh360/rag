"""
角色管理API路由
管理员用于管理系统角色和权限
"""
import json
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.connection import get_db
from app.models.database import Role, User
from app.middleware.auth import require_role_management, get_current_admin_user

router = APIRouter(prefix="/api/roles", tags=["角色管理"])


def parse_permissions(permissions: Any) -> Dict[str, bool]:
    """解析权限字段,兼容字符串、列表和字典类型"""
    if isinstance(permissions, str):
        try:
            parsed = json.loads(permissions)
            # 如果解析后是列表,转换为字典
            if isinstance(parsed, list):
                return {perm: True for perm in parsed}
            elif isinstance(parsed, dict):
                return parsed
            else:
                return {}
        except json.JSONDecodeError:
            return {}
    elif isinstance(permissions, list):
        # 直接是列表,转换为字典
        return {perm: True for perm in permissions}
    elif isinstance(permissions, dict):
        return permissions
    else:
        return {}


# Pydantic 模型
class RoleCreate(BaseModel):
    """创建角色请求模型"""
    name: str
    description: str | None = None
    permissions: Dict[str, bool] = {}


class RoleUpdate(BaseModel):
    """更新角色请求模型"""
    name: str | None = None
    description: str | None = None
    permissions: Dict[str, bool] | None = None


class RoleResponse(BaseModel):
    """角色响应模型"""
    id: int
    name: str
    description: str | None = None
    permissions: Dict[str, bool]
    user_count: int = 0
    created_at: str | None = None


class RoleListResponse(BaseModel):
    """角色列表响应模型"""
    total: int
    roles: List[RoleResponse]


@router.get("", response_model=RoleListResponse)
async def get_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management)
):
    """
    获取角色列表
    - 包含每个角色的用户数量
    """
    roles = db.query(Role).all()

    role_responses = []
    for role in roles:
        # 统计使用该角色的用户数
        user_count = db.query(User).filter(User.role_id == role.id).count()

        role_responses.append(RoleResponse(
            id=role.id,
            name=role.name,
            description=role.description,
            permissions=parse_permissions(role.permissions),
            user_count=user_count,
            created_at=role.created_at
        ))

    return RoleListResponse(total=len(role_responses), roles=role_responses)


@router.get("/{role_id}", response_model=RoleResponse)
async def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management)
):
    """获取单个角色详情"""
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )

    # 统计使用该角色的用户数
    user_count = db.query(User).filter(User.role_id == role.id).count()

    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=parse_permissions(role.permissions),
        user_count=user_count,
        created_at=role.created_at
    )


@router.post("", response_model=RoleResponse)
async def create_role(
    role_data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management)
):
    """
    创建新角色
    - 需要管理员权限
    - 检查角色名唯一性
    """
    # 检查角色名是否已存在
    existing_role = db.query(Role).filter(Role.name == role_data.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="角色名已存在"
        )

    # 创建新角色
    new_role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions
    )

    db.add(new_role)
    db.commit()
    db.refresh(new_role)

    return RoleResponse(
        id=new_role.id,
        name=new_role.name,
        description=new_role.description,
        permissions=parse_permissions(new_role.permissions),
        user_count=0,
        created_at=new_role.created_at
    )


@router.put("/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management)
):
    """
    更新角色信息
    - 需要管理员权限
    - 不能修改系统内置角色(id <= 3)的名称
    """
    # 获取要更新的角色
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )

    # 防止修改系统内置角色的名称
    if role_id <= 3 and role_data.name is not None and role_data.name != role.name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能修改系统内置角色的名称"
        )

    # 更新角色名
    if role_data.name is not None and role_data.name != role.name:
        existing = db.query(Role).filter(
            Role.name == role_data.name,
            Role.id != role_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="角色名已存在"
            )
        role.name = role_data.name

    # 更新描述
    if role_data.description is not None:
        role.description = role_data.description

    # 更新权限
    if role_data.permissions is not None:
        role.permissions = role_data.permissions

    db.commit()
    db.refresh(role)

    # 统计使用该角色的用户数
    user_count = db.query(User).filter(User.role_id == role.id).count()

    return RoleResponse(
        id=role.id,
        name=role.name,
        description=role.description,
        permissions=parse_permissions(role.permissions),
        user_count=user_count,
        created_at=role.created_at
    )


@router.delete("/{role_id}")
async def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management)
):
    """
    删除角色
    - 需要管理员权限
    - 不能删除系统内置角色(id <= 3)
    - 不能删除仍有用户使用的角色
    """
    # 获取要删除的角色
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )

    # 不能删除系统内置角色
    if role_id <= 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除系统内置角色"
        )

    # 检查是否有用户使用该角色
    user_count = db.query(User).filter(User.role_id == role_id).count()
    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该角色仍有 {user_count} 个用户使用,无法删除"
        )

    db.delete(role)
    db.commit()

    return {"message": "角色删除成功", "role_id": role_id}


@router.get("/{role_id}/permissions", response_model=Dict[str, bool])
async def get_role_permissions(
    role_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management)
):
    """
    获取角色的权限配置
    - 返回该角色的所有权限项
    """
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )

    return parse_permissions(role.permissions)


@router.put("/{role_id}/permissions")
async def update_role_permissions(
    role_id: int,
    permissions: Dict[str, bool],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role_management)
):
    """
    更新角色的权限配置
    - 完全替换该角色的权限配置
    """
    role = db.query(Role).filter(Role.id == role_id).first()

    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="角色不存在"
        )

    role.permissions = permissions
    db.commit()
    db.refresh(role)

    return {"message": "权限更新成功", "permissions": parse_permissions(role.permissions)}
