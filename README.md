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

# 或 智谱（GLM-4-Flash-250414 官方免费模型）
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash-250414
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

全免费方案：GitHub + Supabase + Render + Vercel。

### 1. 推送代码到 GitHub

```powershell
cd E:\TripAI
git remote add origin https://github.com/<你的用户名>/TripAI.git
git branch -M main
git push -u origin main
```

`.env` / `.env.local` 已被 .gitignore 排除，密钥不会上传。

### 2. Supabase 数据库（免费）

1. 打开 [supabase.com](https://supabase.com) 注册并创建项目（区域选新加坡或东京，延迟更低）
2. 左侧 Database → Connect → **Transaction mode（端口 6543）** 的连接串复制
3. 把连接串里的 `[YOUR-PASSWORD]` 换成数据库密码

### 3. Render 后端（免费）

1. 打开 [render.com](https://render.com) 注册（用 GitHub 登录最快）
2. New → Web Service → 选择 TripAI 仓库
3. 配置：
   - Root Directory: `backend`
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. 添加环境变量：
   - `DATABASE_URL` = Supabase 连接串
   - `JWT_SECRET_KEY` = 本地 backend/.env 里那个随机密钥
   - `LLM_BASE_URL` = `https://api.siliconflow.cn/v1`
   - `LLM_API_KEY` = 硅基流动 Key
   - `LLM_MODEL` = `deepseek-ai/DeepSeek-V4-Flash`
   - `AMAP_WEB_KEY` = 高德 Web 服务 Key
   - `CORS_ORIGINS` = `["https://<你的vercel域名>.vercel.app"]`
5. 部署完成后记录后端地址（形如 `https://xxx.onrender.com`）

> 免费档空闲 15 分钟后会休眠，首次访问要等 30~60 秒冷启动，属正常现象。

### 4. Vercel 前端（免费）

1. 打开 [vercel.com](https://vercel.com) 注册（GitHub 登录）
2. New Project → 导入 TripAI 仓库 → Root Directory 选 `frontend`
3. 添加环境变量：
   - `NEXT_PUBLIC_API_URL` = `https://xxx.onrender.com`（后端地址）
   - `NEXT_PUBLIC_AMAP_JS_KEY` = 高德 JS API Key
4. 部署完成后得到 `https://xxx.vercel.app`

### 5. 高德白名单

去 [高德控制台](https://console.amap.com/dev/key/app) 编辑 JS API Key，
把 `https://xxx.vercel.app` 加入域名白名单（Web 服务 Key 无需配置）。

### 6. 上线验证

手机浏览器打开 `https://xxx.vercel.app`，注册/登录 → 创建旅行 → 生成行程 → 地图定位 → 分享页，
全流程走一遍即部署成功。

## 手机使用（PWA）

前端是移动端优先设计，手机浏览器直接可用；部署后还支持"添加到主屏幕"：

- 规划页在小屏自动切换为「行程 / 地图 / 详情」三个标签页
- 编辑行程时底部有固定的「保存 / 取消」操作栏
- 导航栏在小屏显示汉堡菜单
- iOS Safari：分享按钮 → 添加到主屏幕
- Android Chrome：菜单 → 安装应用 / 添加到主屏幕

手机要能访问，需要先把前后端部署到公网（见上），然后把
`NEXT_PUBLIC_API_URL` 指向后端域名。

## 迭代路线

- **V1.0**（当前）：AI 规划 + 地图 + 登录 + 编辑 + 分享
- **V1.5**：照片上传 + AI 自动生成旅行日志（Photo 表已预留）
- **V2.0**：多人协作编辑
- **V3.0**：AI 实时旅行助手
