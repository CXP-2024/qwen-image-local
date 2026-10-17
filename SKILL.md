---
name: qwen-image-local
description: "使用本机 Qwen Image 2.1 Turbo 编辑图片、按多图参考替换动漫角色，检查已有 ComfyUI 环境并保存可追溯结果。用于明确要求本地 Qwen 生图或修图；不用于视频生成、普通换脸或自动下载模型。"
---

# 本地 Qwen Image 2.1 Turbo

使用现有本地部署，不重新下载权重或创建另一套 Python 环境。当前保留方案是 Turbo INT8 ConvRot、官方精确 8 步、Euler、CPU/default KV cache、约 1MP 像素预算。主模型的 INT8 与 KV cache INT8 是两件事；后者在本机失败过，不作为默认。

## 环境与调用

先用任意可用 Python 执行本 skill 的 `scripts/qwen_local.py doctor`。它只读取本地文件、队列和显卡状态；服务未启动与文件缺失分开报告。部署位置、启动方法与环境变量见 [local-runtime.md](references/local-runtime.md)。

编辑用 `scripts/qwen_local.py edit --images 原图.png 参考图.png --prompt-file 提示词.txt --label 名称`。提示词保存 UTF-8，图序和 `<image1>`、`<image2>` 标签一致。先加 `--dry-run` 可验证输入、权重及实际采样图，不启动服务、不领取显卡锁、不提交或写入任务。

真正编辑前查看 doctor 的 running/pending 队列、GPU 锁和 GPU 进程；存在其他重任务时等待，不能结束别的项目或另开实例抢卡。服务未启动且已确认空闲时，按本地参考中的命令隐藏启动现有服务，保存 PID/启动时间和日志，再等 `/system_stats` 就绪。脚本不会替用户自动启动服务。

`edit` 固定 Turbo/CPU/default，支持 1–10 张图，默认 resolution 1024、seed 20261012。脚本复用现有 runner，输出与逐次工作流、输入/输出哈希、提示词、prompt_id、耗时在程序目录 `tests/output` 与 `tests/jobs`。POST 结果不确定或超时先查历史和队列，不删除锁重发。非本机服务不在此 skill 的运行范围内。

## 编辑与角色参考

只修改用户要求部分，明确必须保留的动作、表情、其他人物、背景和文字。身份来自角色参考，构图与表演来自原片，不能把失败旧 AI 图当新编辑底图。

动漫角色替换优先用原片帧＋目标头部局部＋目标衣服局部，逐张说明职责。完整站姿立绘可能把非站立动作带偏；裁剪仅隔离身份/衣装，不改变原片底图。示例见 [prompting.md](references/prompting.md)。这些是本地已测起点，不保证所有角色和画风都合适。

## 审核与交付

读取实际生成原图，检查脸、发饰、衣装、手脚、遮挡和要求保留的人物；既看全图也放大易错部位。背景或文字“保持”指令不保证像素不变。生成成功记候选，不等同生产验收。给用户实际输出与记录路径、耗时、尺寸及可见偏差。单帧结果不证明连续视频一致性，不自动追加视频或整片制作。
