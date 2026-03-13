# JWT 包安装问题修复

## 问题描述

项目在运行时出现 `AttributeError: module 'jwt' has no attribute 'encode'` 错误。

## 根本原因

项目的虚拟环境中安装了错误的 `jwt` 包 (版本 1.4.0),而不是正确的 `PyJWT` 包。

- **错误的包**: `jwt` 1.4.0 - 这是一个不同的包,没有 `encode` 和 `decode` 方法
- **正确的包**: `PyJWT` 2.x - 这才是我们需要的 JWT 库

## 修复方法

```bash
# 1. 卸载错误的 jwt 包
pip uninstall -y jwt

# 2. 安装正确的 PyJWT 包
pip install PyJWT

# 3. 验证安装
python -c "import jwt; print(f'JWT version: {jwt.__version__}')"
```

## 预防措施

在 `requirements.txt` 中明确指定包名:

```
PyJWT>=2.8.0  # 正确 ✅
# 不要使用: jwt  # 错误 ❌
```

## 验证测试

```python
from app.services.auth import AuthService

auth = AuthService()
token = auth.create_access_token({'user_id': 1, 'sub': 'testuser'})
payload = auth.verify_token(token, 'access')
print(f"Token验证成功: {payload}")
```

## 相关修改

- 已修复异常处理: 使用通用 `Exception` 替代 `jwt.PyJWTError`
- 已移除不必要的 jwt 导入
