# 架构设计

## 总体架构

```text
Vue Query Workbench
        |
        v
FastAPI REST API
        |
        +--> Auth & Session Service
        |      |
        |      +--> SQLite users
        |      +--> SQLite sessions
        |
        +--> Connection Store(SQLite)
        |
        +--> Driver Factory
              |
              +--> MySQL Client
              +--> ClickHouse Client
              +--> StarRocks Client
```

## 后端分层

### API 层

负责接收前端请求、参数校验、异常转换。

### Service 层

负责统一编排：

- 用户注册、登录、会话识别
- 连接测试
- 连接配置持久化
- 数据库/表元数据查询
- SQL 执行

### Driver 层

每种数据库对应一个 Client，实现统一接口：

- `test_connection()`
- `list_databases()`
- `list_tables(database)`
- `execute_query(sql, limit, database)`

这样可以方便后续新增：

- PostgreSQL
- Doris
- Oracle
- SQLServer

## 核心设计点

### 1. 多数据库统一抽象

通过工厂模式，根据 `db_type` 创建不同数据库客户端。

### 2. 只读安全控制

当前实现限制为：

- `SELECT`
- `SHOW`
- `DESCRIBE`
- `DESC`
- `EXPLAIN`
- `WITH`

同时拒绝多语句和常见 DDL / DML 关键字。

### 3. 前后端分离

前端只负责：

- 登录表单与当前用户态展示
- 表单输入
- 元数据展示
- SQL 编辑和结果渲染

后端负责：

- 认证与会话校验
- 按用户隔离连接配置
- 驱动适配
- 连接管理
- SQL 安全控制
- 结果标准化输出

### 4. 用户级资源隔离

连接配置存储在 SQLite 中，并带有 `owner_user_id` 字段。

后端在以下场景强制校验当前用户：

- 查看连接列表
- 删除连接
- 浏览数据库和表
- 执行 SQL

这保证了用户登录后只能访问自己的配置和查询上下文。

## 后续扩展建议

### 连接治理

- 连接分组
- 环境标签（开发 / 测试 / 生产）
- 密钥托管
- 连接池

### 查询治理

- 查询超时
- 查询取消
- 行列数限制
- 下载 CSV / Excel
- SQL 格式化
- 查询收藏夹

### 权限治理

- 用户体系
- 角色权限
- 审计日志
- 数据脱敏
