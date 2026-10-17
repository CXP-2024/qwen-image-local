# 本机部署与启动

确认日期：2026-10-17。本 skill 绑定已有 Windows 部署，不包含模型、ComfyUI 或 Python 安装器。

| 内容 | 位置 |
|---|---|
| 程序/配置/工作流/结果 | `%USERPROFILE%\Documents\QwenImage21` |
| 权重（已迁移） | `H:\models\QwenImage21` |
| Python | `%USERPROFILE%\Documents\MiniMaxH3\.venv\Scripts\python.exe` |
| ComfyUI | `%USERPROFILE%\Documents\MiniMaxH3\ComfyUI` |
| API / 网页 | `http://127.0.0.1:8765` |

`QWEN_IMAGE_PROJECT` 可覆盖程序目录，`QWEN_IMAGE_PYTHON` 可覆盖运行 Python。模型根目录以程序目录 `extra_model_paths.yaml` 的 `qwen_image21.base_path` 为准，不假定 C 盘仍有权重。脚本依赖该部署内 `work/run_edit.py`、`workflows/community_edit_api.json`、`sources/turbo_model_index.json`；脱离本机时须先提供兼容部署再运行 doctor。

保留三份必需文件共约 17.28 GB：

- `diffusion_models/qwen_image_2.1_turbo_int8_convrot.safetensors`
- `text_encoders/qwen3vl_8b_int8_convrot.safetensors`
- `vae/qwen_image_2.1_vae_bf16.safetensors`

普通版已删除，不自动重新下载。完整使用说明在程序目录 `使用说明.md`。UI 导入 `workflows/turbo_edit_ui.json`；该画布以单图编辑为起点，多图编辑可用 skill 脚本。

## 启动已有服务

先核查 GPU 与全部现有 Comfy 队列。doctor 默认检查 8188–8195、8765、18290，可用 `QWEN_COMFY_PORTS`（逗号分隔）增加端口；不把未检测到的其他服务当成空闲。系统有其他 worker 时按用户现有队列协调。

授权编辑且资源可用时，可在 PowerShell 启动（服务已运行则直接复用，不重复启动）：

```powershell
$project = Join-Path $env:USERPROFILE 'Documents\QwenImage21'
$runtime = Join-Path $env:USERPROFILE 'Documents\MiniMaxH3'
$python = Join-Path $runtime '.venv\Scripts\python.exe'
$serverMain = Join-Path $runtime 'ComfyUI\main.py'
$argsList = @('-u', "`"$serverMain`"", '--listen', '127.0.0.1', '--port', '8765', '--extra-model-paths-config', "`"$project\extra_model_paths.yaml`"", '--input-directory', "`"$project\tests\input`"", '--output-directory', "`"$project\tests\output`"", '--disable-all-custom-nodes', '--disable-auto-launch', '--preview-method', 'none')
$serviceProcess = Start-Process -FilePath $python -ArgumentList $argsList -WindowStyle Hidden -PassThru -RedirectStandardOutput "$project\work\comfy_stdout.log" -RedirectStandardError "$project\work\comfy_stderr.log"
@{ Id=$serviceProcess.Id; StartTime=$serviceProcess.StartTime.ToString('o') } | ConvertTo-Json | Set-Content -LiteralPath "$project\work\server_process.json"
```

轮询 `/system_stats` 就绪后提交，不把进程启动等同加载成功。关闭服务前确认队列空闲并核对自己记录的 PID 与启动时间；不要停止其他服务。用户也可手动双击程序目录 `启动QwenImage21.cmd`。

## 已测配置与限制

Turbo sigmas：`1, 0.978453, 0.95418, 0.926626, 0.89508, 0.845148, 0.704534, 0.414568, 0`，不是任意八步调度。resolution 1024 为约 1MP 预算；1920×1080 输入在已测案例输出 1376×768。

RTX 5080 历史双图编辑 Turbo 约 11–12 秒，三图约 19 秒，均是指定样例执行时间；冷启动、输入数量、负载会改变速度。CPU/default 缓存是本机可用配置；不要承诺显存永远够用。
