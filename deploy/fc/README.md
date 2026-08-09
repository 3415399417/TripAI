# TripAI 阿里云函数计算（FC）部署

前后端全部托管在阿里云 FC（杭州），国内访问快，无需 Docker / 容器镜像。

## 线上地址

- 前端：`https://tripai-web-gvoujitbkf.cn-hangzhou.fcapp.run`
- 后端：`https://tripai-api-gvspoitbkf.cn-hangzhou.fcapp.run`

## 前置条件

- 阿里云账号 + AccessKey（RAM 子账号需函数计算权限）
- 本机安装 [Serverless Devs](https://www.serverless-devs.com/)（`npm i -g @serverless-devs/s`）
- 登录并配置 access：

```bash
s config add --AccessKeyID <AK> --AccessKeySecret <SK> -a tripai
```

## 后端部署

```bash
# 1. 构建依赖包并组装 api-code（含 app/ server.py python/）
#    参考：把后端代码复制到 api-code/，用 pip download 拉取
#    Linux 依赖 wheel 到 python/（见下方“依赖打包”）

# 2. 导出环境变量（密钥不入库）
$env:DATABASE_URL="postgresql://postgres.xxx@...:5432/postgres"
$env:JWT_SECRET_KEY="..."
$env:LLM_BASE_URL="https://api.siliconflow.cn/v1"
$env:LLM_API_KEY="..."
$env:LLM_MODEL="deepseek-ai/DeepSeek-V4-Flash"
$env:LLM_TIMEOUT_SECONDS="240"
$env:AMAP_WEB_KEY="..."

# 3. 部署
s deploy -y -t s-api.yaml
```

注意：Supabase 请使用 **session pooler 端口 5432**（6543 是 transaction
pooler，与 psycopg 的 prepared statements 不兼容，会导致
`DuplicatePreparedStatement` 报错）。

## 前端部署

```bash
# 1. 构建 Next.js standalone（生产 API 地址必须指向后端 FC）
cd ../../frontend
$env:NEXT_PUBLIC_API_URL="https://tripai-api-gvspoitbkf.cn-hangzhou.fcapp.run"
npm run build

# 2. 组装 web-code（在 deploy/fc 下执行）
#    - 复制 .next/standalone/* 到 web-code/
#    - 复制 .next/static 到 web-code/.next/static
#    - 复制 public/ 到 web-code/public

# 3. 导出后端地址并部署
$env:BACKEND_API_URL="https://tripai-api-gvspoitbkf.cn-hangzhou.fcapp.run"
s deploy -y -t s-web.yaml
```

## 依赖打包（后端 python/）

FC 的 custom.debian10 自带 Python 3.10，依赖 wheel 需为 manylinux：

```bash
pip download -r requirements.txt --platform manylinux2014_x86_64 `
  --python-version 310 --implementation cp --only-binary=:all: -d wheels
# 纯 Python 包（如 exceptiongroup）单独下载解压：
pip download exceptiongroup --no-deps -d wheels
```

将 wheel 解压到 `api-code/python/`，保留 `*.dist-info` 目录。

## 高德地图白名单

在 [高德控制台](https://console.amap.com/dev/key/app) 的 JS API Key
白名单中添加前端域名：

```
https://tripai-web-gvoujitbkf.cn-hangzhou.fcapp.run
```
