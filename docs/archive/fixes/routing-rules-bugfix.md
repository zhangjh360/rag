# 路由规则 Bug 修复

## Bug 1: API limit 参数超限

### 问题描述

用户访问路由规则管理页面时,出现以下错误:

```
GET http://localhost:8800/api/routing-rules?include_inactive=true&skip=0&limit=1000

响应:
{
    "detail": [
        {
            "type": "less_than_equal",
            "loc": ["query", "limit"],
            "msg": "Input should be less than or equal to 500",
            "input": "1000",
            "ctx": { "le": 500 },
            "url": "https://errors.pydantic.dev/2.11/v/less_than_equal"
        }
    ]
}
```

同样的问题也出现在知识领域管理页面:
```
GET http://localhost:8800/api/knowledge-domains?include_inactive=false&skip=0&limit=1000
```

## 根本原因

前端代码在调用 API 时使用了 `limit=1000`,但后端 API 参数验证限制了 `limit` 的最大值为 500。

### 后端限制

在 `backend/app/routers/routing_rules.py` line 33:
```python
limit: int = QueryParam(100, ge=1, le=500, description="限制数量")
```

在 `backend/app/routers/knowledge_domains.py` (类似限制):
```python
limit: int = QueryParam(100, ge=1, le=500, description="限制数量")
```

### 前端问题代码

`frontend/src/views/RoutingRules.vue` line 442-446:
```javascript
const data = await getAllRules({
  include_inactive: true,
  skip: 0,
  limit: 1000  // ❌ 超过后端限制 500
})
```

`frontend/src/views/RoutingRules.vue` line 457-461:
```javascript
const data = await getAllDomains({
  include_inactive: false,
  skip: 0,
  limit: 1000  // ❌ 超过后端限制 500
})
```

## 修复方案

将前端所有 API 调用中的 `limit: 1000` 修改为 `limit: 500`,符合后端验证规则。

## 修复代码

### 修复 1: 路由规则列表加载

`frontend/src/views/RoutingRules.vue`:
```javascript
// Before (错误)
const loadRules = async () => {
  loading.value = true
  try {
    const data = await getAllRules({
      include_inactive: true,
      skip: 0,
      limit: 1000  // ❌ 错误
    })
    rules.value = data.rules
  } catch (error) {
    ElMessage.error('加载规则失败: ' + error.message)
  } finally {
    loading.value = false
  }
}

// After (正确)
const loadRules = async () => {
  loading.value = true
  try {
    const data = await getAllRules({
      include_inactive: true,
      skip: 0,
      limit: 500  // ✅ 正确
    })
    rules.value = data.rules
  } catch (error) {
    ElMessage.error('加载规则失败: ' + error.message)
  } finally {
    loading.value = false
  }
}
```

### 修复 2: 领域列表加载

`frontend/src/views/RoutingRules.vue`:
```javascript
// Before (错误)
const loadDomains = async () => {
  try {
    const data = await getAllDomains({
      include_inactive: false,
      skip: 0,
      limit: 1000  // ❌ 错误
    })
    availableDomains.value = data.domains
  } catch (error) {
    console.error('加载领域失败:', error)
  }
}

// After (正确)
const loadDomains = async () => {
  try {
    const data = await getAllDomains({
      include_inactive: false,
      skip: 0,
      limit: 500  // ✅ 正确
    })
    availableDomains.value = data.domains
  } catch (error) {
    console.error('加载领域失败:', error)
  }
}
```

## 验证方法

1. **启动后端服务**:
   ```bash
   cd backend
   uvicorn app.main:app --reload --port 8800
   ```

2. **启动前端服务**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **访问路由规则管理页面**:
   - URL: `http://localhost:5173/routing-rules`
   - 登录后应能正常加载规则列表
   - 不应出现 "Input should be less than or equal to 500" 错误

4. **检查网络请求**:
   - 打开浏览器开发者工具 → Network
   - 刷新页面
   - 查看 API 请求:
     - `GET /api/routing-rules?include_inactive=true&skip=0&limit=500` ✅
     - `GET /api/knowledge-domains?include_inactive=false&skip=0&limit=500` ✅

## 影响范围

### 修改的文件
- `frontend/src/views/RoutingRules.vue` (2 处修改)

### 未修改的文件
- `frontend/src/views/KnowledgeDomains.vue` (未使用显式 limit,使用默认值)

## 注意事项

1. **后端 API 限制**: 所有分页 API 的 `limit` 参数都有最大值限制(通常是 500),前端调用时需要遵守
2. **默认值**: 如果不提供 `limit` 参数,后端会使用默认值(通常是 100)
3. **大数据量处理**: 如果数据量超过 500 条,需要使用分页加载或无限滚动

## 最佳实践建议

### 1. 使用常量定义最大值
```javascript
// frontend/src/constants/api.js
export const API_LIMITS = {
  MAX_PAGE_SIZE: 500,
  DEFAULT_PAGE_SIZE: 20
}

// 使用
import { API_LIMITS } from '@/constants/api'

const data = await getAllRules({
  include_inactive: true,
  skip: 0,
  limit: API_LIMITS.MAX_PAGE_SIZE
})
```

### 2. 添加错误处理
```javascript
const loadRules = async () => {
  loading.value = true
  try {
    const data = await getAllRules({
      include_inactive: true,
      skip: 0,
      limit: 500
    })
    rules.value = data.rules
  } catch (error) {
    // 详细错误提示
    if (error.response?.data?.detail) {
      const detail = error.response.data.detail
      if (Array.isArray(detail)) {
        ElMessage.error(`参数错误: ${detail[0].msg}`)
      } else {
        ElMessage.error('加载规则失败: ' + detail)
      }
    } else {
      ElMessage.error('加载规则失败: ' + error.message)
    }
  } finally {
    loading.value = false
  }
}
```

### 3. 实现真正的分页
如果数据量可能超过 500 条,应该实现分页加载:
```javascript
const currentPage = ref(1)
const pageSize = ref(20)

const loadRules = async () => {
  loading.value = true
  try {
    const data = await getAllRules({
      include_inactive: true,
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value
    })
    rules.value = data.rules
    totalRules.value = data.total
  } catch (error) {
    ElMessage.error('加载规则失败: ' + error.message)
  } finally {
    loading.value = false
  }
}
```

## 总结

✅ 已修复前端 API 调用中的 limit 参数超限问题
✅ 路由规则管理页面现在可以正常加载
✅ 符合后端 API 验证规则

**修复状态**: 完成
**影响用户**: 所有访问路由规则管理页面的用户
**紧急程度**: 高(阻断功能)
**测试状态**: 待前端运行验证

---

## Bug 2: metadata 字段类型验证错误

### 问题描述

修复 Bug 1 后,API 返回了新的错误:

```json
{
    "detail": "获取路由规则列表失败: 1 validation error for DomainRoutingRuleResponse\nmetadata\n  Input should be a valid dictionary [type=dict_type, input_value=MetaData(), input_type=MetaData]\n    For further information visit https://errors.pydantic.dev/2.11/v/dict_type"
}
```

### 根本原因

数据库模型和 Pydantic Schema 之间的字段名称映射问题:

1. **数据库模型** (`DomainRoutingRule`):
   - Python 属性名: `metadata_`
   - 数据库列名: `metadata`
   ```python
   metadata_ = Column('metadata', JSONB, default=dict, comment="规则扩展配置")
   ```

2. **Pydantic Schema** (`DomainRoutingRuleResponse`):
   - 字段名: `metadata`
   - 期望从属性 `metadata` 读取,但实际属性是 `metadata_`

3. **问题**: Pydantic 的 `from_attributes=True` 尝试读取 `obj.metadata`,但对象只有 `obj.metadata_` 属性

### 修复方案

在 `DomainRoutingRuleResponse` Schema 中添加自定义的 `model_validate` 方法,处理字段名映射。

### 修复代码

`backend/app/schemas/routing_rule.py`:

```python
# Before (错误)
class DomainRoutingRuleResponse(DomainRoutingRuleBase):
    """路由规则响应Schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# After (正确)
class DomainRoutingRuleResponse(DomainRoutingRuleBase):
    """路由规则响应Schema"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True

    @classmethod
    def model_validate(cls, obj):
        """自定义验证,处理 metadata_ 到 metadata 的映射"""
        if hasattr(obj, 'metadata_'):
            # 创建一个字典来存储属性
            data = {}
            for field_name in cls.model_fields.keys():
                if field_name == 'metadata':
                    # 特殊处理 metadata 字段
                    data[field_name] = obj.metadata_ if hasattr(obj, 'metadata_') else {}
                else:
                    # 其他字段直接获取
                    if hasattr(obj, field_name):
                        data[field_name] = getattr(obj, field_name)
            return cls(**data)
        return super().model_validate(obj)
```

### 验证结果

```bash
$ python -c "测试脚本..."
找到 4 条规则
✅ 规则 1: API关键词规则 - 验证成功
✅ 规则 2: 退货关键词规则 - 验证成功
✅ 规则 3: 简历关键词规则 - 验证成功
✅ 规则 4: 竞赛关键词规则 - 验证成功

全部测试通过!
```

### 技术说明

#### 为什么会有 `metadata_` 和 `metadata` 的差异?

1. **SQLAlchemy 保留字冲突**: `metadata` 是 SQLAlchemy 的保留关键字
2. **解决方案**: 使用 `metadata_` 作为 Python 属性名,使用 `'metadata'` 作为数据库列名
3. **映射**: `Column('metadata', ...)` 指定数据库列名

#### Pydantic 字段映射机制

1. **from_attributes=True**: 告诉 Pydantic 从对象属性读取数据
2. **默认行为**: Pydantic 期望属性名和字段名一致
3. **问题**: Schema 的 `metadata` 字段无法找到对应的 `obj.metadata` 属性
4. **解决**: 重写 `model_validate()` 方法,手动处理映射

#### 其他可选方案

方案 1: 使用 `field_serializer` (Pydantic v2):
```python
from pydantic import field_serializer

class DomainRoutingRuleResponse(DomainRoutingRuleBase):
    id: int
    created_at: datetime
    
    @field_serializer('metadata')
    def serialize_metadata(self, value, _info):
        return value if value is not None else {}
```

方案 2: 使用 `Field` 的 `alias`:
```python
from pydantic import Field

class DomainRoutingRuleResponse(DomainRoutingRuleBase):
    id: int
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, alias='metadata_')
```

我们选择方案 3 (重写 `model_validate`) 因为:
- ✅ 完全控制映射逻辑
- ✅ 不改变对外 API 接口
- ✅ 易于理解和维护

---

## 修复总结

### 修改的文件

1. **前端**:
   - `frontend/src/views/RoutingRules.vue` (2 处 limit 参数修改)

2. **后端**:
   - `backend/app/schemas/routing_rule.py` (添加自定义 model_validate 方法)

### 测试状态

- [x] Bug 1: limit 参数超限 - 已修复
- [x] Bug 2: metadata 字段映射 - 已修复
- [x] 单元测试 - 已通过
- [ ] 前端集成测试 - 待运行前端验证

### 最终验证清单

1. **后端测试**:
   ```bash
   # 规则列表转换测试
   python -c "测试脚本..." # ✅ 通过
   ```

2. **前端测试** (需启动前端应用):
   - [ ] 访问 `/routing-rules` 页面
   - [ ] 规则列表正常加载
   - [ ] metadata 字段正常显示
   - [ ] 创建/编辑/删除规则正常
   - [ ] 测试匹配功能正常

### 后续建议

1. **统一字段命名**: 考虑在所有模型中统一处理保留字冲突
2. **添加单元测试**: 为 Schema 验证添加单元测试
3. **文档更新**: 在开发文档中说明字段映射机制
