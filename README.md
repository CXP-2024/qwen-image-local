# qwen-image-local

用于 Codex 的本地 Qwen Image 2.1 Turbo 图片编辑 skill，支持单图编辑和多参考动漫角色替换。此仓库是现有 Windows 部署的调用与操作层，**不包含模型、ComfyUI、Python 环境或素材**，也不会自动下载它们。

## 安装

在已准备兼容 Qwen Image 2.1 部署的电脑上，将仓库克隆到 Codex skills 目录：

```powershell
git clone git@github.com:CXP-2024/qwen-image-local.git "$env:USERPROFILE\.codex\skills\qwen-image-local"
```

本机已直接安装到该位置，无需再次克隆。重新打开聊天后可显式调用 `$qwen-image-local`；skill 本身允许自动发现。

已有部署默认位置为 `%USERPROFILE%\Documents\QwenImage21`，运行 Python 为 `%USERPROFILE%\Documents\MiniMaxH3\.venv\Scripts\python.exe`。可通过 `QWEN_IMAGE_PROJECT`、`QWEN_IMAGE_PYTHON` 覆盖。权重由部署内 `extra_model_paths.yaml` 配置，本机在 `H:\models\QwenImage21`。所需运行文件与启动说明见 [local-runtime.md](references/local-runtime.md)。

## 使用

```powershell
$skillRoot = Join-Path $env:USERPROFILE '.codex\skills\qwen-image-local'
python "$skillRoot\scripts\qwen_local.py" doctor
python "$skillRoot\scripts\qwen_local.py" edit --images 'D:\images\source.png' 'D:\images\head.png' 'D:\images\costume.png' --prompt-file 'D:\images\prompt.txt' --dry-run
```

确认环境、输入与 GPU 队列后，启动已有服务，去掉 `--dry-run` 提交编辑。默认是 Turbo、官方 8 步、CPU/default 缓存、resolution 1024。doctor 读取队列/GPU 状态；dry-run 验证采样图但不会提交任务或启动服务。

脚本复用部署里的 `work/run_edit.py`。新机器须先提供该部署及配套工作流；仅克隆本 skill 不等于安装模型。结果位于部署目录 `tests/output`，任务记录位于 `tests/jobs`。

身份替换、动作保留、手脚、画风和其他人物需分别审核。输出成功不等于生产验收；单帧测试不证明视频一致性。提示词示例见 [prompting.md](references/prompting.md)。
