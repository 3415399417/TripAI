# TripAI · AI 智能旅行规划与行程管理平台

输入目的地、预算、兴趣和人群，AI 自动生成每日行程；地图可视化、按天天气、真实花费记账、一键导航、精美分享卡片一应俱全。个人练手 + 求职案例定位，全流程可 0 成本跑通。

> 后端 15 条自动化测试 + 前端类型检查已接入 GitHub Actions（CI 全绿）。

## 功能特性

**AI 生成**
- 创建旅行：目的地、日期、人数、预算、兴趣、节奏、旅行类型、随行人群
- SSE 流式生成进度：预算分析 → AI 规划行程 → 地点核对 → 生成方案，全程可见、不干等
- 消费知识库：城市消费系数 × 四档消费等级（经济/舒适/高品质/奢华）× 兴趣权重 × 季节价格 × 人群约束
- 预算方案：消费画像、建议消费区间、预算分配、日均预算（预算代表消费能力，不必花完）
- 备选推荐：预算不足/天气不好/想升级时的替换方案
- 推荐理由：结合人群、天气、兴趣的口语化表达

**行程管理**
- 每日行程卡片可折叠，默认展开第一天
- 编辑行程：上移/下移/增删地点、改时间/时长/花费
- 高德地图：地点打点、路线连线、点击查看详情
- 一键导航：地点卡片直接跳转高德 App 导航
- 地点详情：营业时间、电话、图片（高德 POI 懒加载 + 缓存）

**出行辅助**
- 行程天气：实时天气 + 按天预报（超过 4 天预报窗口自动提示，AI 生成天气兜底）
- 真实花费记账：预算/已花费/结余对比，超支变红，支持分类与备注
- 公开分享页：无需登录即可查看完整行程
- 分享卡片：上传背景图、拖动调整位置、一键下载 PNG，发朋友圈/小红书

**工程化**
- PWA：手机可“添加到主屏幕”独立使用
- 生成日志与提示词版本管理（`generation_logs` / `prompt_versions`）
- GitHub Actions：后端测试 + 前端类型检查自动执行

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Next.js 15 + React 19 + TypeScript + Tailwind CSS 4 + PWA |
| 后端 | FastAPI + SQLAlchemy 2 + Pydantic v2 + JWT |
| 数据库 | MySQL 8（生产，阿里云 RDS）/ SQLite（零配置本地/测试） |
| 地图 | 高德 JS API（前端）+ 高德 Web 服务 API（后端 POI 搜索，带本地缓存） |
| AI | DeepSeek 官方（OpenAI 兼容，可切换硅基流动 / 智谱） |
| 部署 | 阿里云函数计算 FC 3.0（杭州），CI 用 GitHub Actions |

## 项目结构

```
TripAI/
├── backend/                     # FastAPI 后端
│   ├── app/
│   │   ├── core/                # 配置、数据库、安全（JWT/bcrypt）、轻量迁移
│   │   ├── models/              # User / Trip / Schedule / Place / Photo /
│   │   │                        # PromptVersion / GenerationLog / TripExpense
│   │   ├── schemas/             # Pydantic 请求/响应模型
│   │   ├── api/                 # 路由：auth / trips / ai / places
│   │   ├── data/                # 专家知识库：城市系数 / 消费等级 / 兴趣权重 /
│   │   │                        # 节奏 / 季节 / 人群约束 / 标志性地点
│   │   └── services/
│   │       ├── ai_service/      # LLM 生成（generator/prompt/client/budget/optimizer/saver/mock）
│   │       ├── amap_service.py  # 高德 POI 搜索 + 详情（本地缓存）
│   │       └── weather_service.py  # 高德天气：实时 + 按天预报（30 分钟缓存）
│   ├── scripts/seed.py          # 演示账号 + 演示行程
│   ├── tests/                   # 15 条测试：预算规则/天气/记账/地点详情/SSE 流式/冒烟
│   └── .env.example             # 环境变量模板
├── frontend/                    # Next.js 前端
│   ├── app/                     # 首页/登录/注册/我的旅行/创建/行程详情/分享
│   ├── components/              # TripForm / ItineraryList / MapView / PlaceCard /
│   │                            # TripWeatherCard / TripExpenseCard / ShareCardModal ...
│   ├── lib/                     # API 客户端（含 SSE 流式读取）、类型、天气工具
│   └── public/                  # PWA manifest / sw.js / 图标
├── .github/workflows/           # ci.yml（测试+类型检查）、deploy.yml（FC 手动部署）
├── deploy/fc-backend/           # 阿里云 FC 后端部署配置（含密钥，已 gitignore）
├── deploy/fc-frontend/          # 阿里云 FC 前端部署配置（含密钥，已 gitignore）
├── start-all.bat                # 一键启动前后端
└── docker-compose.yml           # 可选：本地 PostgreSQL
```

## 快速开始（Windows）

### 一键启动（推荐）

双击 `E:\TripAI\start-all.bat`，会弹出两个窗口：
- 后端窗口出现 `Application startup complete`
- 前端窗口出现 `Ready`

然后访问 http://localhost:3000 ，手机连同一 WiFi 访问 http://192.168.31.67:3000 。

### 手动启动

```powershell
# 1. 后端
cd E:\TripAI\backend
py -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env        # 按需填入 Key（见下方配置）
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 2. 前端（另开一个终端）
cd E:\TripAI\frontend
npm install
Copy-Item .env.local.example .env.local   # 填入高德 JS Key
npm run dev -- -H 0.0.0.0
```

演示账号（需先执行 `python scripts\seed.py`）：`demo@tripai.cn` / `demo123456`

### 跑测试

```powershell
cd E:\TripAI\backend
python -m pytest tests -q        # 15 passed
```

## 环境变量

### 后端 `backend/.env`（模板见 `.env.example`）

```ini
# 数据库：本地零配置用 SQLite，生产用 MySQL
DATABASE_URL=sqlite:///./tripai.db

# 安全：生产环境务必换随机串
JWT_SECRET_KEY=change-me-to-a-random-string

# CORS 白名单（JSON 数组）
CORS_ORIGINS=["http://localhost:3000"]

# AI（DeepSeek 官方；可切换硅基流动 / 智谱）
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=
LLM_MODEL=deepseek-chat
LLM_TIMEOUT_SECONDS=180

# 高德 Web 服务 Key（后端 POI 搜索）
AMAP_WEB_KEY=
```

`LLM_API_KEY` 留空时后端自动进入 mock 模式，返回示例行程，方便先跑通全流程。

### 前端 `frontend/.env.local`

```ini
# 后端地址（本地开发指向本机；部署时指向线上后端）
NEXT_PUBLIC_API_URL=http://192.168.31.67:8000
# 高德 Web 端(JS API) Key
NEXT_PUBLIC_AMAP_JS_KEY=
```

> ⚠️ 高德 Web 服务 Key 只能放后端，绝不能写进前端代码。

## 0 成本配置指南

### 高德地图（个人开发者免费）

1. 注册并实名认证：[高德开放平台](https://console.amap.com/dev/id/phone)（免费）
2. 创建两个 Key：
   - **Web 端 (JS API)** → 填到 `frontend/.env.local` 的 `NEXT_PUBLIC_AMAP_JS_KEY`（页面地图）
   - **Web 服务** → 填到 `backend/.env` 的 `AMAP_WEB_KEY`（POI 搜索 / 天气）
3. JS API Key 需要把访问域名加入白名单（本地开发加 `http://192.168.31.67:3000`）。

> 个人配额有限，本项目对 POI 搜索和天气都做了数据库/内存缓存，实际消耗很低。

### AI 模型（三选一）

```ini
# DeepSeek 官方（便宜）
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat

# 或 硅基流动
LLM_BASE_URL=https://api.siliconflow.cn/v1
LLM_MODEL=deepseek-ai/DeepSeek-V4-Flash

# 或 智谱（GLM-4-Flash 官方免费模型）
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash-250414
```

## CI/CD

推送到 `main` 分支后，[GitHub Actions](https://github.com/3415399417/TripAI/actions) 自动执行：

- `backend-tests`：后端 15 条 pytest 用例（SQLite + mock LLM，无需任何 Key）
- `frontend-checks`：TypeScript 类型检查（`tsc --noEmit`）

`deploy.yml` 为阿里云 FC 手动部署工作流（`workflow_dispatch`），在仓库 Secrets 配置
`ALIBABA_CLOUD_ACCESS_KEY_ID` / `ALIBABA_CLOUD_ACCESS_KEY_SECRET` 后可在 Actions 页面手动触发。

## 部署（阿里云 FC + MySQL RDS）

当前线上架构：前端/后端均部署在阿里云函数计算 FC 3.0（杭州），数据库用阿里云 RDS MySQL。

### 后端

```powershell
cd E:\TripAI\deploy\fc-backend
s deploy -y
```

部署配置（`s.yaml`）内含环境变量（数据库、JWT、LLM、高德），已通过 `.gitignore` 排除，不会进仓库。
部署后永久 API 地址：`https://tripai-api-gvspoitbkf.cn-hangzhou.fcapp.run`

### 前端

```powershell
cd E:\TripAI\frontend
$env:NEXT_PUBLIC_API_URL = "https://tripai-api-gvspoitbkf.cn-hangzhou.fcapp.run"
npm run build
cd E:\TripAI\deploy\fc-frontend
s deploy -y
```

> ⚠️ 注意：阿里云 FC 的默认域名（`*.fcapp.run`）会把网页强制作为附件下载，**只适合 API**；
> 网页应用需要绑定自定义域名（国内需 ICP 备案）。日常使用可走本地局域网 + PWA，
> 简历/海外访问可用 Vercel 链接。

## 核心 API

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | /api/auth/register | 注册（返回 JWT） |
| POST | /api/auth/login | 登录 |
| GET | /api/auth/me | 当前用户 |
| GET | /api/trips | 我的旅行列表 |
| GET | /api/trips/{id} | 旅行详情（含行程） |
| PUT | /api/trips/{id}/schedule | 保存编辑后的行程 |
| DELETE | /api/trips/{id} | 删除旅行 |
| GET | /api/trips/{id}/public | 公开分享页 |
| GET | /api/trips/{id}/weather | 行程天气（实时 + 按天预报） |
| GET | /api/trips/{id}/expenses | 记账列表 + 预算汇总 |
| POST | /api/trips/{id}/expenses | 记一笔 |
| DELETE | /api/trips/{id}/expenses/{eid} | 删除记账 |
| GET | /api/trips/{id}/generation-log | 生成日志（Prompt / AI 输出） |
| POST | /api/ai/generate-trip | AI 生成行程 |
| POST | /api/ai/generate-trip-stream | AI 生成（SSE 流式进度） |
| GET | /api/places/search | POI 搜索（带缓存） |
| GET | /api/places/{id}/detail | 地点详情（营业时间/电话/图片） |

接口文档：后端启动后访问 http://127.0.0.1:8000/docs

## 开源参考

- **[TripMind](https://github.com/Ring-Yew/tripmind)**：Next.js + FastAPI 全栈架构参考（agents/services/routes 分层）。
- **[TripKit](https://www.npmjs.com/package/tripkit)**（MIT）：行程数据 schema 与地图可视化思路借鉴。

本项目未直接引入上述依赖，保持轻量、零成本和国产服务（高德 + DeepSeek/硅基流动）优先。

## 迭代路线

- **V1.0**（当前）：AI 规划 + 地图 + 天气 + 记账 + 分享卡片 + 一键导航
- **V1.5**：用户偏好记忆（越用越懂你）、行程导出（日历/PDF）
- **V2.0**：多方案对比、照片游记（Photo 表已预留）
- **V3.0**：多人协作、AI 实时旅行助手
