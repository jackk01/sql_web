# SQL Web Console

一个从零搭建的数据库 Web 查询系统示例，满足以下目标：

- 前后端分离
- 后端使用 Python（FastAPI）
- 前端使用 Vue 3（Vite + Element Plus）
- 支持 MySQL、ClickHouse、StarRocks
- 提供用户登录、个人连接隔离、数据库/表浏览、只读 SQL 查询、结果表格展示
- 查询结果支持导出为 Excel

## 项目结构

```text
sql_web/
├── backend/                  # FastAPI 服务
│   ├── app/
│   │   ├── api/              # REST API
│   │   ├── core/             # 配置
│   │   ├── models/           # Pydantic 模型
│   │   ├── services/         # 数据库连接与查询服务
│   │   └── storage/          # 连接配置存储
│   └── requirements.txt
├── frontend/                 # Vue 3 + Vite 前端
└── docs/
    └── architecture.md
```

## 功能设计

### 1. 连接管理

- 每个用户只管理自己的数据库连接
- 测试连接可用性
- 按数据库类型动态给出默认端口
- 当前示例将用户、会话、连接配置保存到本地 SQLite3 文件

### 2. 用户认证与隔离

- 支持本地用户名密码注册与登录
- 使用 HttpOnly Cookie 保存会话
- 后端所有连接相关接口按当前登录用户强制过滤
- 数据库连接密码做应用层加密存储

### 3. 元数据浏览

- 拉取数据库列表
- 拉取指定数据库下的表列表
- 支持前端快速切换连接与数据库

### 4. SQL 查询工作台

- 浏览器页面输入 SQL
- 后端统一转发到不同数据库驱动
- 仅允许只读语句，避免误操作
- 返回结构化结果，前端表格直接渲染
- 支持将当前查询结果导出为 Excel

## 技术选型

### 后端

- FastAPI: 提供 API、类型约束与自动文档
- sqlite3: 存储用户、会话与连接配置
- PyMySQL: 连接 MySQL / StarRocks
- clickhouse-connect: 连接 ClickHouse
- cryptography: 加密数据库连接密码
- Pydantic: 请求与响应建模

### 前端

- Vue 3 + TypeScript
- Vite
- Element Plus

## 启动方式

### 启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

后端默认地址：`http://127.0.0.1:8000`

首次启动时会在 `backend/data/` 下自动创建：

- `app.db`：SQLite 数据文件
- `app.key`：连接密码加密密钥

### 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认地址：`http://127.0.0.1:5173`

## API 概览

- `GET /api/v1/health`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`
- `GET /api/v1/db-types`
- `GET /api/v1/connections`
- `POST /api/v1/connections`
- `DELETE /api/v1/connections/{id}`
- `POST /api/v1/connections/test`
- `GET /api/v1/connections/{id}/databases`
- `GET /api/v1/connections/{id}/tables?database=xxx`
- `POST /api/v1/query/execute`
- `POST /api/v1/query/export`

## 生产化建议

- 将本地账号体系替换为公司 SSO / OIDC
- 将本地文件密钥替换为 KMS / Vault
- 引入 RBAC、审计日志、SQL 黑白名单
- 使用 SQL 解析器替代简单正则校验
- 增加分页查询、导出下载、收藏 SQL、查询历史
- 对接 SSO 与多环境权限隔离
