# DJtransGAN Mix Studio

本地研究用工作区：在官方 DJtransGAN 之上加了 **FastAPI + Vue 混音工作台**，方便上传两首歌、设 cue、跑推理并试听。

License: **MIT**

## 相关仓库

本工作区在本地会并排放四个仓库（根目录 `.gitignore` 会忽略后三个，避免嵌套提交）：

| 仓库 | 说明 |
| --- | --- |
| **[HKLHaoBin/DJtransGAN](https://github.com/HKLHaoBin/DJtransGAN)**（本仓库） | Mix Studio 外壳：`server/` + `web/` + 启动脚本 |
| **[HKLHaoBin/DJtransGAN-code](https://github.com/HKLHaoBin/DJtransGAN-code)** | 模型 / 训练 / 推理代码（fork 自官方实现，含本地推理补丁） |
| **[HKLHaoBin/DJtransGAN-demo-site](https://github.com/HKLHaoBin/DJtransGAN-demo-site)** | ICASSP 2022 论文试听页与示例音频 |
| **[HKLHaoBin/DJtransGAN-dg-pipeline](https://github.com/HKLHaoBin/DJtransGAN-dg-pipeline)** | 训练数据生成管线 |

上游论文与官方仓库：

- 论文：[arXiv:2110.06525](https://arxiv.org/abs/2110.06525)
- 官方模型：[ChenPaulYu/DJtransGAN](https://github.com/ChenPaulYu/DJtransGAN)
- 官方 demo：[ChenPaulYu/djtransgan-icassp2022](https://github.com/ChenPaulYu/djtransgan-icassp2022)
- 官方管线：[ChenPaulYu/DJtransGAN-dg-pipeline](https://github.com/ChenPaulYu/DJtransGAN-dg-pipeline)

## 本地目录结构

```text
DJtransGAN/                 ← 本仓库（Mix Studio）
├── server/                 FastAPI 推理与 job 队列
├── web/                    Vue 3 + Vite 前端
├── code/                   → clone DJtransGAN-code
├── demo-site/              → clone DJtransGAN-demo-site
├── dg-pipeline/            → clone DJtransGAN-dg-pipeline
├── tools/rubberband/       rubberband CLI（Windows）
└── results/                推理输出（本地，不入库）
```

建议克隆方式：

```bash
git clone https://github.com/HKLHaoBin/DJtransGAN.git
cd DJtransGAN
git clone https://github.com/HKLHaoBin/DJtransGAN-code.git code
git clone https://github.com/HKLHaoBin/DJtransGAN-demo-site.git demo-site
git clone https://github.com/HKLHaoBin/DJtransGAN-dg-pipeline.git dg-pipeline
```

## 环境

```powershell
cd DJtransGAN
.\activate.ps1
```

- 依赖见 `requirements-inference.txt`（不要直接装 `code/requirements.txt` 那份 2021 冻结列表）
- `.venv/`、`.cache/` 建议放在本目录，避免污染系统盘
- `rubberband`：激活脚本会把 `tools\rubberband` 加入 `PATH`

## Mix 工作台

两个终端：

```powershell
# 终端 1 — API
.\start-api.ps1

# 终端 2 — Vue
.\start-web.ps1
```

- 前端：http://127.0.0.1:5173/
- API：http://127.0.0.1:8010/（文档 `/docs`，健康检查 `/api/health`）

页面：

1. **Mix** — 上传 Prev/Next、设 cue、跑混音、听 short/full、看曲线  
2. **Results** — 历史任务  
3. **Demo** — 论文对照试听  
4. **Settings / About**

首次启动若缺少权重，会尝试下载到本地 `pretrained/`（开发态在仓库旁的数据目录；安装版在 `%LOCALAPPDATA%\DJtransGAN\pretrained`）。上传优先 **wav/flac**。同一时间只跑一个 job。

> 模型输出是研究原型级过渡（单声道 + 时频 masking），不是母带级立体声混音。

## CLI 推理

与网页共用 `server/engine.py`：

```powershell
.\activate.ps1
cd code
python script/inference.py --download 1 --out_dir ../results/inference
```

## 仅试听 Demo 页

```powershell
cd demo-site
python -m http.server 8765
```

或打开上游在线 demo：https://chenpaulyu.github.io/djtransgan-icassp2022/

## 发布 / Windows 安装包

推送到 `main`、推送 `v*` tag，或在 Actions 里手动运行 **Windows Release**，会：

1. 相对最新 `v*` tag 自动 **patch +1**（手动 tag 则使用该版本）
2. 构建 Vue 前端，用 PyInstaller 打成 Windows onedir EXE（内嵌前端 + `code/` + rubberband）
3. 用 Inno Setup 生成 `DJtransGAN-Setup-<version>.exe`
4. 发布到 GitHub Release（另附 portable zip）

安装后：

| 项 | 位置 |
| --- | --- |
| 程序 | `Program Files\DJtransGAN` |
| 用户数据（结果 / 权重） | `%LOCALAPPDATA%\DJtransGAN` |
| 卸载 | Windows「应用和功能」（默认保留用户数据） |

本地打包（需已 clone `code/`，并完成 `web` 生产构建）：

```powershell
cd web; npm ci; npm run build; cd ..
pip install -r requirements-inference.txt
pip install -r packaging/requirements-desktop.txt
pip install -r packaging/requirements-build.txt
pip install madmom --no-build-isolation
# 建议使用 CPU torch wheel
pyinstaller packaging/DJtransGAN.spec --noconfirm
# 安装 Inno Setup 后：
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DAppVersion=0.1.0 packaging\installer.iss
```

桌面入口（开发态，需先 `npm run build` 才有同域前端）：

```powershell
.\activate.ps1
python -m server.desktop
```
