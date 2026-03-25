---
name: python-expert
description: Write idiomatic Python code — PEP 8, type hints, clean & concise，Python Code Generation Guidelines
---

# Python Expert

## Instructions

# Python Code Generation Guidelines

## Always Apply These Rules

1. **Be concise** — prefer builtins, comprehensions, walrus operator when appropriate
2. **Type hints mandatory** — every function signature needs type hints
3. **No redundant code** — don't write what Python gives you for free
4. **Modern Python** — assume Python 3.10+, use union types, match/case, etc.
5. **Docstrings** — Google-style for public APIs, skip for trivial helpers

【Python 代码规范】
1. 遵循 PEP 8 + 项目目录结构约定
2. snake_case 命名，无缩写
3. 类/异常：PascalCase + AppError 基类
4. 导入顺序：标准库 → 第三方 → 本地模块
5. 分层清晰：views → services → models/repositories
6. EAFP 错误处理，自定义异常继承 AppError
7. 使用 Pydantic 做输入校验和序列化
8. 使用 SQLAlchemy ORM，约定表名为复数
9. 单元测试用 pytest，测试文件在 tests/ 目录
10. DRY — 无重复代码，无魔法字符串/数字
11. Convention Over Configuration（COC）-约定大于配置 — 遵循项目既定的目录结构、命名规范，减少显式配置
12. KISS-Keep It Simple, Stupid — 保持简单，优先用最直接的方案
13. YAGNI-You Aren't Gonna Need It — 不做过度设计，不要为"将来可能用到"添加代码



## Code Patterns to Prefer

- `lambda` + builtins (`map`, `filter`, `sorted`) for simple transforms
- `itertools` for complex iteration
- `dataclasses` or `attrs` for data containers
- Context managers for file/connection handling
- f-strings over .format() or %

## Code Patterns to Avoid

- `for i in range(len(lst))` → use `enumerate()`
- `tmp = []; for x in items: tmp.append(f(x))` → use comprehension
- Multiple return statements in simple functions → return expressions directly
- Classes for namespaced functions → use modules instead
- Unnecessary intermediate variables

## Example Refactoring

Before:
```python
def get_squares(nums):
    result = []
    for n in nums:
        result.append(n ** 2)
    return result
    
After:
def get_squares(nums: list[int]) -> list[int]:
    return [n**2 for n in nums]
	

# 模块名：全小写，下划线分隔（snake_case）
# ❌ user_controller  utils/helper_funcs
# ✅ user_controller  utils/helpers

# 类名：大驼峰（PascalCase）
class UserService:
    pass

# 函数/方法名：小写下划线（snake_case）
def get_user_by_id(user_id: int) -> dict:
    pass

# 常量：全大写下划线
MAX_RETRY_COUNT = 3

# 私有成员：单下划线前缀（约定）或双下划线（强制）
def _private_helper(self):  # 约定私有
    pass

# 文件与目录：全小写、复数名词优先
# users/models.py  而非  user/model.py

# 1. 单一职责（SRP）
# ❌ 一个函数做太多事情
# ✅ 每个函数只做一件事

def create_user(name: str, email: str) -> dict:
    # 只负责创建，不做校验、不发邮件、不写日志
    pass

# 2. 依赖注入（类比 Rails 的依赖注入）
class UserService:
    def __init__(self, user_repo: UserRepository):
        self._repo = user_repo  # 通过注入而非硬编码

# 3. 分层清晰
# views/controllers  → 接收请求、参数校验
# services           → 业务逻辑
# repositories/models → 数据访问
# schemas            → 数据序列化/校验

# 标准顺序：标准库 → 第三方库 → 本地模块
# 各组之间空一行

import os
import json
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import User
from app.schemas import UserCreate

# Python 风格：EAFP（先尝试，后道歉）
# 与 Rails 的 rescue_from 理念相通

# ❌ 防御式编程
if os.path.exists(config_path):
    with open(config_path) as f:
        pass

# ✅ EAFP 风格
try:
    with open(config_path) as f:
        pass
except FileNotFoundError:
    # 优雅降级或抛出业务异常
    raise ConfigNotFoundError(f"Missing config: {config_path}")

# 自定义异常类（类比 Rails 自定义 Error）
class AppError(Exception):
    """基础异常，所有业务异常继承此类"""
    status_code = 500

class ValidationError(AppError):
    status_code = 400
	
# 使用 Pydantic（类比 Rails 的 ActiveModel::Validations）
from pydantic import BaseModel, EmailStr, validator

class UserCreate(BaseModel):
    email: EmailStr
    password: str

    @validator("password")
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
		
# 使用 SQLAlchemy（类比 Rails ORM 风格）
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"  # 约定表名：复数、小写下划线

    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
	
# 使用 pytest（类比 Rails RSpec 风格）
# 文件命名：test_*.py 或 *_test.py
# 函数命名：test_*_should_*

class TestUserService:
    def test_create_user_should_return_user_dict(self):
        # Arrange
        repo = MockUserRepository()
        service = UserService(repo)

        # Act
        result = service.create("test@example.com")

        # Assert
        assert result["email"] == "test@example.com"


# 使用 .env + python-dotenv（类比 Rails .env）
# 生产绝不提交 .env
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    secret_key: str

    class Config:
        env_file = ".env"


