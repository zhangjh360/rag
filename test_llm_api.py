#!/usr/bin/env python3
"""
测试LLM多模型管理API
"""

import os
import sys

# 添加后端路径
sys.path.insert(0, '/home/zhangjh/code/python/rag/backend')

# 设置环境变量
os.environ['DB_URL'] = 'sqlite:///./test.db'
os.environ['SKIP_CONFIG_VALIDATION'] = 'true'

from sqlalchemy import create_engine, Column, Integer, String, Text, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

# 创建基础模型
Base = declarative_base()

class LLMGroup(Base):
    __tablename__ = 'llm_groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    models = relationship("LLMModel", back_populates="group", cascade="all, delete-orphan")

class LLMModel(Base):
    __tablename__ = 'llm_models'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    api_key = Column(Text)
    base_url = Column(String(255))
    group_id = Column(Integer, ForeignKey('llm_groups.id'))
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    temperature = Column(Float, default=0.7)
    max_tokens = Column(Integer, default=2000)
    top_p = Column(Float, default=1.0)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    group = relationship("LLMGroup", back_populates="models")
    scenarios = relationship("LLMScenario", back_populates="default_model")

class LLMScenario(Base):
    __tablename__ = 'llm_scenarios'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    default_model_id = Column(Integer, ForeignKey('llm_models.id'))
    is_active = Column(Boolean, default=True)
    created_at = Column(String(50), nullable=False)
    updated_at = Column(String(50), nullable=False)

    default_model = relationship("LLMModel", back_populates="scenarios")

# 创建数据库连接
engine = create_engine('sqlite:///./test.db', echo=True)
Base.metadata.create_all(bind=engine)

# 创建会话
Session = sessionmaker(bind=engine)
db = Session()

# 创建测试数据
def create_test_data():
    now = datetime.now().isoformat()

    # 创建分组
    group1 = LLMGroup(
        name='fast-models',
        display_name='快速模型',
        description='响应速度快的模型',
        sort_order=1,
        is_active=True,
        created_at=now,
        updated_at=now
    )

    group2 = LLMGroup(
        name='precise-models',
        display_name='精确模型',
        description='准确率高的模型',
        sort_order=2,
        is_active=True,
        created_at=now,
        updated_at=now
    )

    db.add_all([group1, group2])
    db.commit()
    db.refresh(group1)
    db.refresh(group2)

    # 创建模型
    model1 = LLMModel(
        name='gpt-3.5-turbo',
        display_name='GPT-3.5 Turbo',
        provider='openai',
        model_name='gpt-3.5-turbo',
        group_id=group1.id,
        is_default=True,
        is_active=True,
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        created_at=now,
        updated_at=now
    )

    model2 = LLMModel(
        name='gpt-4',
        display_name='GPT-4',
        provider='openai',
        model_name='gpt-4',
        group_id=group2.id,
        is_default=False,
        is_active=True,
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        created_at=now,
        updated_at=now
    )

    model3 = LLMModel(
        name='claude-3',
        display_name='Claude 3',
        provider='anthropic',
        model_name='claude-3',
        group_id=group2.id,
        is_default=False,
        is_active=True,
        temperature=0.7,
        max_tokens=2000,
        top_p=1.0,
        created_at=now,
        updated_at=now
    )

    db.add_all([model1, model2, model3])
    db.commit()
    db.refresh(model1)
    db.refresh(model2)
    db.refresh(model3)

    # 创建场景
    scenario1 = LLMScenario(
        name='conversation',
        display_name='日常对话',
        description='用于一般性对话的场景',
        default_model_id=model1.id,
        is_active=True,
        created_at=now,
        updated_at=now
    )

    scenario2 = LLMScenario(
        name='code-generation',
        display_name='代码生成',
        description='用于代码生成的场景',
        default_model_id=model2.id,
        is_active=True,
        created_at=now,
        updated_at=now
    )

    db.add_all([scenario1, scenario2])
    db.commit()

    print("✅ 测试数据创建成功!")
    return group1, group2, model1, model2, model3, scenario1, scenario2

# 查询和验证数据
def verify_data():
    print("\n📊 验证数据:")

    # 查询分组
    groups = db.query(LLMGroup).all()
    print(f"\n🔹 模型分组 ({len(groups)}个):")
    for group in groups:
        models_count = len(group.models)
        print(f"  - {group.display_name} ({group.name}): {models_count} 个模型")

    # 查询模型
    models = db.query(LLMModel).all()
    print(f"\n🔹 模型列表 ({len(models)}个):")
    for model in models:
        group_name = model.group.display_name if model.group else '未分组'
        print(f"  - {model.display_name} ({model.provider}) - 分组: {group_name} - 状态: {'激活' if model.is_active else '停用'}")

    # 查询场景
    scenarios = db.query(LLMScenario).all()
    print(f"\n🔹 场景配置 ({len(scenarios)}个):")
    for scenario in scenarios:
        model_name = scenario.default_model.display_name if scenario.default_model else '未设置'
        print(f"  - {scenario.display_name}: 默认模型 = {model_name}")

    print("\n✅ 数据验证完成!")

# 测试CRUD操作
def test_crud():
    print("\n🧪 测试CRUD操作:")

    # 创建新分组
    now = datetime.now().isoformat()
    new_group = LLMGroup(
        name='test-group',
        display_name='测试分组',
        description='这是一个测试分组',
        sort_order=3,
        is_active=True,
        created_at=now,
        updated_at=now
    )
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    print(f"✅ 创建分组: {new_group.display_name}")

    # 更新分组
    new_group.description = '更新后的测试分组'
    new_group.updated_at = datetime.now().isoformat()
    db.commit()
    print(f"✅ 更新分组: {new_group.display_name}")

    # 删除分组
    db.delete(new_group)
    db.commit()
    print(f"✅ 删除分组: test-group")

    print("\n✅ CRUD操作测试完成!")

if __name__ == '__main__':
    print("🚀 开始测试LLM多模型管理系统\n")

    try:
        # 创建测试数据
        create_test_data()

        # 验证数据
        verify_data()

        # 测试CRUD
        test_crud()

        print("\n✨ 所有测试通过!")
        print("\n数据库文件: /home/zhangjh/code/python/rag/backend/test.db")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()
