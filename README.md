# DJtransGAN 研究工作区

本地研究用，依赖与缓存都在本目录（`F:\编程\DJtransGAN`），不往 C 盘写 pip/torch 缓存。

## 目录

| 目录 | 用途 |
| --- | --- |
| `code/` | [DJtransGAN](https://github.com/ChenPaulYu/DJtransGAN) 模型 / 训练 / 推理 |
| `demo-site/` | 论文试听页 + `assets/audios` |
| `dg-pipeline/` | 训练数据生成管线 |
| `server/` | FastAPI：推理引擎 + 异步 jobs |
| `web/` | Vue 3 + Vite Mix 工作台 |
| `tools/rubberband/` | rubberband CLI（官方 Windows 包） |

## 环境

```powershell
cd "F:\编程\DJtransGAN"
.\activate.ps1
```

- `.venv/`、`.cache/pip`、`.cache/torch` 均在本目录
- 临时解压：`F:\djtransgan-tmp`（避免中文路径下 sdist 解压失败）
- `rubberband`：激活脚本会把 `tools\rubberband` 加入 PATH

依赖见 `requirements-inference.txt`（不要装 `code/requirements.txt` 那份 2021 整机冻结列表）。

## Mix 工作台（推荐）

两个终端：

```powershell
# 终端 1 — API（模型常驻内存）
cd "F:\编程\DJtransGAN"
.\start-api.ps1

# 终端 2 — Vue
cd "F:\编程\DJtransGAN"
.\start-web.ps1
```

- 前端：http://127.0.0.1:5173/
- API：http://127.0.0.1:8010/ （文档 `/docs`，健康检查 `/api/health`）

> 若本机 `8000` 被代理占用，默认改用 `8010`。Vite 已将 `/api` 代理到该端口。

页面：

1. **Mix** — 上传 Prev/Next、设 cue、跑混音、听 short/full、看 fader/EQ 曲线
2. **Demo** — 论文 8 组对照试听
3. **About** — 说明

首次启动若缺少权重，会尝试经 gdown 下载到 `code/pretrained/`。

上传优先 **wav/flac**；自测可用 `code/test/` 两首歌、默认 cue（prev=96 / next=30）。同一时间只跑一个 job，后续请求会排队。

## CLI 推理

与网页共用 `server/engine.py`：

```powershell
.\activate.ps1
cd code
python script/inference.py --download 1 --out_dir ../results/inference
```

## 纯试听（不启 FastAPI）

```powershell
cd demo-site
& "F:\编程\DJtransGAN\.venv\Scripts\python.exe" -m http.server 8765
```

或打开 https://chenpaulyu.github.io/djtransgan-icassp2022/
