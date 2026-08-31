# DJtransGAN 研究工作区

本地研究用，依赖与缓存都在本目录（`F:\编程\DJtransGAN`），不往 C 盘写 pip/torch 缓存。

## 为何用官方仓库而不是 fork

查过 GitHub fork：普遍 0 star、与上游 identical，没有更好的可视化或推理改进。  
真正带试听页的是作者自己的 demo 仓库，因此这里克隆官方三件套：

| 目录 | 仓库 | 用途 |
| --- | --- | --- |
| `code/` | [ChenPaulYu/DJtransGAN](https://github.com/ChenPaulYu/DJtransGAN) | 模型、训练、推理 |
| `demo-site/` | [ChenPaulYu/djtransgan-icassp2022](https://github.com/ChenPaulYu/djtransgan-icassp2022) | 论文试听页 + `assets/audios` |
| `dg-pipeline/` | [ChenPaulYu/DJtransGAN-dg-pipeline](https://github.com/ChenPaulYu/DJtransGAN-dg-pipeline) | 训练数据生成管线 |

在线 demo（若自定义域名挂了）：https://chenpaulyu.github.io/djtransgan-icassp2022/

## 环境（已建好）

- 虚拟环境：`.venv/`（Python 3.10，包装在此，不在 C 盘 user site）
- pip 缓存：`.cache/pip`
- torch 缓存：`.cache/torch`
- 解压临时目录：`F:\djtransgan-tmp`（纯 ASCII；中文路径会导致部分 sdist 解压失败）

激活：

```powershell
cd "F:\编程\DJtransGAN"
.\activate.ps1
```

已装好推理主依赖：`torch 2.2.2`、`torchaudio`、`librosa`、`nnAudio`、`torchlibrosa`、`openunmix`、`gdown` 等。

**尚未装上 `madmom`**（拍点/小节线，推理预处理需要）：需本机安装 [Microsoft C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)，然后：

```powershell
.\activate.ps1
pip install "madmom==0.16.1" --no-build-isolation
```

另需系统里有 **rubberband** CLI（`pyrubberband` 变速），Windows 可从 https://breakfastquay.com/rubberband/ 获取并加入 PATH。

## 试听 demo（本地，推荐先听这个）

```powershell
cd "F:\编程\DJtransGAN\demo-site"
& "F:\编程\DJtransGAN\.venv\Scripts\python.exe" -m http.server 8765
```

浏览器打开：http://127.0.0.1:8765/

也可直接听：`demo-site\assets\audios\1\gan.wav`（与 `linear` / `rule` / `human` 对照）。

在线镜像：https://chenpaulyu.github.io/djtransgan-icassp2022/

## 推理（madmom + rubberband 就绪后）

```powershell
.\activate.ps1
cd code
python script/inference.py --download 1 --out_dir ../results/inference
```

预训练权重经 gdown 落到 `code/pretrained/`。

`code/djtransgan/config/settings.py` 已改成指向本工作区的 `../dg-pipeline` 与 `../results`。

## 原版 requirements 说明

`code/requirements.txt` 是 2021 整机冻结列表（含 `cupy-cuda102` 等），不要直接装。  
用根目录 `requirements-inference.txt`。
