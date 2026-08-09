# TripAI · AI 智能旅行规划与行程管理平台

输入旅行需求，AI 自动生成每日行程，地图可视化展示，支持编辑、AI 重新优化和一键分享。个人练手 + 求职案例定位，全流程 0 成本可跑通。

## 功能

- 注册 / 登录（JWT 认证，bcrypt 密码加密）
- 创建旅行：目的地、日期、人数、预算、兴趣标签、旅行节奏
- AI 行程生成：LLM 输出结构化 JSON，后端 Pydantic 校验 + 高德 POI 坐标校正
- 地图可视化：高德 JS API 打点、路线连线、点击查看详情
- 行程编辑：上移/下移/增删地点、修改时间/时长/花费、AI 重新优化路线
- 公开分享页：无需登录即可查看
- 演示模式：未配置 LLM Key 时自动返回示例行程，流程完整可体验

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 15 + React 19 + TypeScript + Tailwind CSS 4 |
| 后端 | FastAPI + SQLAlchemy 2 + Pydantic v2 |
| 数据库 | SQLite（默认零配置）/ PostgreSQL（Supabase 或 Docker） |
| 地图 | 高德 JS API（前端展示）+ 高德 Web 服务 API（后端 POI 搜索，带本地缓存） |
| AI | OpenAI 兼容协议，可切换 DeepSeek / 硅基流动 / 智谱 |

## 项目结构

```
TripAI/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── core/            # 配置、数据库、安全（JWT/bcrypt）
│   │   ├── models/          # SQLAlchemy：User / Trip / Place / Schedule / Photo
│   │   ├── schemas/         # Pydantic 请求/响应模型
│   │   ├── api/             # 路由：auth / trips / ai / places
│   │   └── services/        # ai_service（LLM + mock）、amap_service（POI 缓存）
│   ├── scripts/seed.py      # 演示账号 + 演示行程
│   └── tests/               # 冒烟测试
├── frontend/                # Next.js 前端
│   ├── app/                 # 页面：首页/登录/注册/我的旅行/创建/规划/分享
│   ├── components/          # Navbar / MapView / TripForm / ItineraryList / PlaceCard
│   └── lib/                 # API 客户端、类型定义
└── docker-compose.yml       # 可选：本地 PostgreSQL
```

## 快速开始（Windows）

### 1. 启动后端

```powershell
cd E:\TripAI\backend
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python scripts\seed.py        # 可选：创建演示账号和演示行程
uvicorn app.main:app --reload --port 8000
```

### 2. 启动前端

```powershell
cd E:\TripAI\frontend
npm install
npm run dev                   # http://localhost:3000
```

演示账号：`demo@tripai.cn` / `demo123456`

### 3. 跑测试

```powershell
cd E:\TripAI\backend
pytest tests -q
```

## 0 成本配置指南

### 高德地图（个人开发者免费）

1. 注册并实名认证：[高德开放平台](https://console.amap.com/dev/id/phone)（免费，需身份证 + 人脸识别）
2. 创建两个 Key：
   - **Web 端 (JS API)** → 填到 `frontend/.env.local` 的 `NEXT_PUBLIC_AMAP_JS_KEY`（页面地图）
   - **Web 服务** → 填到 `backend/.env` 的 `AMAP_WEB_KEY`（POI 搜索）
3. 个人配额：POI 搜索 100 次/天，路径规划/地理编码 5000 次/天。本项目把搜索结果缓存进数据库，实际一天用不完 100 次。

> ⚠️ Web 服务 Key 只能放后端，绝不能写进前端代码。

### AI 模型（三选一，OpenAI 兼容）

在 `backend/.env` 配置：

```ini
# DeepSeek 官方（便宜，需充值）
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 或 硅基流动（注册送 2000 万 tokens，0 成本）
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=deepseek-ai/DeepSeek-V3

# 或 智谱（GLM-4-Flash 官方免费模型）
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash
```

`LLM_API_KEY` 留空时后端自动进入 mock 模式，返回示例行程，方便先跑通全流程。

### PostgreSQL / Supabase

默认用 SQLite 零配置运行。切换 PostgreSQL：

```powershell
cd E:\TripAI
docker compose up -d          # 本地 PostgreSQL
# backend/.env:
DATABASE_URL=postgresql+psycopg://tripai:tripai@localhost:5432/tripai
```

部署到 Supabase 时，把连接串填到 `DATABASE_URL` 即可（免费档 500MB）。

## 核心 API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/auth/register | 注册（返回 JWT） |
| POST | /api/auth/login | 登录 |
| GET | /api/auth/me | 当前用户 |
| GET | /api/trips | 我的旅行列表 |
| GET | /api/trips/{id} | 旅行详情（含行程） |
| PUT | /api/trips/{id} | 修改旅行信息 |
| PUT | /api/trips/{id}/schedule | 保存编辑后的行程 |
| DELETE | /api/trips/{id} | 删除旅行 |
| GET | /api/trips/{id}/public | 公开分享页 |
| POST | /api/ai/generate-trip | AI 生成行程 |
| POST | /api/ai/reoptimize | AI 重新优化路线 |
| GET | /api/places/search | POI 搜索（带缓存） |

接口文档：后端启动后访问 http://127.0.0.1:8000/docs

## 开源参考

- **[TripMind](https://github.com/Ring-Yew/tripmind)**：Next.js + FastAPI 全栈架构参考（agents/services/routes 分层）。
- **[TripKit](https://www.npmjs.com/package/tripkit)**（MIT）：行程数据 schema 与地图可视化思路借鉴。

本项目未直接引入上述依赖，保持轻量、零成本和国产服务（高德 + DeepSeek/硅基流动）优先。

## 部署

- 前端 → Vercel（免费，把 `NEXT_PUBLIC_API_URL` 配成后端域名）
- 后端 → Render / Railway（免费额度内）
- 数据库 → Supabase（免费档）
- 高德 JS API Key 记得在控制台把部署域名加入白名单

## 迭代路线

- **V1.0**（当前）：AI 规划 + 地图 + 登录 + 编辑 + 分享
- **V1.5**：照片上传 + AI 自动生成旅行日志（Photo 表已预留）
- **V2.0**：多人协作编辑
- **V3.0**：AI 实时旅行助手
