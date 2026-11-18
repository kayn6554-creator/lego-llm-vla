# NERO × XR-1：经核实的模型架构与本地实验适配

更新时间：2026-11-18

本文将 **Xiaomi-Robotics-1 官方架构** 与 **NERO 本地适配实验** 分开记录。前者以小米官方网页、论文和公开代码为依据；后者以 `nero-xr1-experiments` 仓库中的模型配置、数据配置、推理 Client 和机制文档为依据。

## 1. 证据边界

| 主题 | 主要证据 | 可以确认的内容 |
|---|---|---|
| XR-1 训练路线与数据 | [小米官方技术介绍](https://robotics.xiaomi.com/xiaomi-robotics-1.html)、[官方仓库](https://github.com/XiaomiRobotics/Xiaomi-Robotics-1) | 100K+ 小时 UMI 预训练、1,700+ 场景、自动状态变化标注、跨本体后训练与指令对齐 |
| XR-1 模型结构 | [官方 XR1.py](https://github.com/XiaomiRobotics/Xiaomi-Robotics-1/blob/main/xr1/mibot/models/VLA/XR1.py) | Qwen3-VL、MoT、36 层 DiT、状态/动作内部张量形状、Flow Matching 采样 |
| Qwen3-VL 配置 | [官方模型配置](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/blob/main/config.json) | 文本主干与视觉塔的层数、维度、注意力头、位置编码和归一化配置 |
| NERO 输入接口 | [NERO Client](https://github.com/kayn6554-creator/nero-xr1-experiments/blob/main/code/collector/nero_vla_client.py) | Front/Wrist RGB、8D 状态、任务指令与 [T,8] 动作回包 |
| 本地模型变体 | [模型演化与机制记录](https://github.com/kayn6554-creator/nero-xr1-experiments/blob/main/docs/model-evolution-and-mechanisms.md)、[M3 配置](https://github.com/kayn6554-creator/nero-xr1-experiments/blob/main/code/xr1-overlay/configs/data/nero3_m3_20261110.yaml)、[M5 配置](https://github.com/kayn6554-creator/nero-xr1-experiments/blob/main/code/xr1-overlay/configs/data/nero3_m5sb_20261112.yaml) | M3/M4/EF4/M5 的动作布局、提示映射、IK 和步骤边界逻辑 |

## 2. XR-1 官方基础架构

### 2.1 两阶段训练路线

1. **Embodiment-free UMI pre-training**：官方介绍称使用超过 100,000 小时的 UMI 操作轨迹，覆盖 1,700 多种场景。长视频被切成定长片段，由 VLM 自动描述夹爪与交互物体的状态变化。
2. **Cross-embodiment post-training**：使用跨本体数据进行本体对齐，并把模型从“根据场景状态变化描述生成动作”进一步对齐到直接遵循自然语言指令。

这里的 100K+ 小时属于 XR-1 官方基础模型训练数据，不是 NERO 本地数据量。

### 2.2 Qwen3-VL-4B-Instruct

XR-1 官方模型配置使用 Qwen3-VL-4B-Instruct。其配置应分成两个部分理解：

- **Vision Tower**：24 层、16 个注意力头、hidden_size=1024、out_hidden_size=2560、patch_size=16。
- **Text Backbone**：36 层、hidden_size=2560、32 个 query heads、8 个 KV heads（GQA）、RoPE、RMSNorm、SiLU gated MLP。

部署侧通过 Hugging Face `AutoProcessor` 处理文本和图像输入。乐高舞台把 Processor、Vision Tower、Text Backbone 拆成三个可见积木，只是教学抽象；真实模型是一个集成的多模态模型，并不是三个独立模型串接。

### 2.3 MoT：VLM 与 DiT 的逐层交互

官方 XR1.py 中，DiT 每一层按层索引读取 VLM 的 `past_key_values`，将缓存的 K/V 与动作侧 K/V 拼接后执行注意力。因此 MoT 是 VLM 与动作专家之间的层级 Transformer 协同方式，不是一个普通的 Linear/MLP Connector。

### 2.4 DiT 与 Flow Matching

官方 XR1.py 明确给出：

- `DiT(layer_num=36, hidden_size=1024)`；
- 每个动作专家层包含注意力、RMSNorm 和 SiLU gated MLP；
- 注意力 head_dim=128，因此动作专家为 8 个注意力头；
- `state_shape=(1,60)`；
- `action_shape=(30,60)`；
- `num_steps=5`。

训练时把噪声与目标动作做时间插值，回归速度目标；推理时从噪声开始，用 5 次 Euler 更新生成动作块。**DiT 是网络，Flow Matching 是训练目标/采样机制**，不能把它们说成两个并列的模型。

官方训练代码还包括候选动作与评分辅助分支：`n_choices=5`，训练时对候选动作和评分计算辅助损失。它不应与部署时的主动作输出混为一谈。

## 3. NERO 本地适配：输入、状态与动作接口

### 3.1 输入与机器人接口

本地 Client 记录：

- `state: float32[8]`：joint1..joint7（rad）+ gripper（m，0–0.1）；
- `images: {front, wrist}`：两路 RGB 图像；
- `prompt: str`：任务指令，可叠加步骤提示；
- 返回 `actions: float[T,8]`：每步 7 个关节绝对目标 + 夹爪目标。

这 8 维是 NERO 的有效物理状态/命令接口。XR-1 官方的 60 维是内部通用容器，不代表 NERO 有 60 个关节。

### 3.2 M3：关节空间多任务基线

M3 使用 `action_layout=nero_joint`、`action_length=30`。它在原有称重、水温、风速任务上新增噪声、红外测温、TDS、pH、土壤温度，形成八类任务。配置包含 11 个数据目录（8 个成功任务目录 + 3 个失败前缀目录），配置生成记录的抽稀后样本数为 107,337，训练 4,026 步。

M3 保留关节空间动作、夹爪绝对目标、静止段抽稀、状态/动作统计和步骤文本。它没有硬性步骤边界机制。

### 3.3 M4：Merge23

M4 在 M3 基础上启用 `step_merge23=true`。物理 Step 2/4 与 Step 3/4 映射为同一条中间阶段文本“move to the target and measure”。网页仍维护四个物理步骤。

Merge23 是提示语义合并，不是硬停止；M4 不会因为检测到动作块边界而自动截断并等待人工确认。

### 3.4 EF4：末端空间 + IK + Merge23

EF/EF4 的有效动作通道：

| 通道 | 含义 |
|---|---|
| 0–2 | 相对 chunk 起点法兰坐标系的位置差 |
| 3–5 | 相对旋转 axis-angle |
| 6 | 夹爪目标 |
| 7 | j3/elbow 冗余消解辅助量 |

输入状态仍是 7 个关节位置 + 夹爪（8D），不是末端状态。推理链路是“末端相对位姿预测 → IK → 关节目标”。EF4 在此基础上增加 Merge23。

EF4 依赖 IK 可解性、运动学模型与关节限位；不能把它与 M3/M4 当作只改变一个变量的严格对照。

### 3.5 M5：Step Flag

M5 使用 `action_layout=nero_joint_sb`：

- 通道 0–7 与 M3 相同；
- 通道 8 是 Step Flag：若未来帧的 `source.step_index` 与 chunk 起始帧不同则标记为 1；
- 标签经 mean/std=0.5/0.5 归一化后作为连续回归输出，因此它不是天然校准的概率；
- 服务端默认阈值 0.5、连续 2 帧触发，找到边界后截断动作块；
- Client 执行边界前动作，暂停等待操作者确认当前物理步骤完成，再更新 step 文件并继续推理；
- 机器人仍只接收 `actions [30,8]`，Step Flag 作为独立诊断字段返回。

**M5 的第 9 个训练通道不是机器人控制命令，也不是任务成功分数。**

## 4. 乐高模型的教学映射

| 乐高积木 | 对应的真实模块 | 说明 |
|---|---|---|
| Qwen3-VL AutoProcessor | `AutoProcessor` | 文本分词与图像预处理 |
| Qwen3-VL Vision Tower | Qwen3-VL vision tower | 24 层视觉编码 |
| Qwen3-VL-4B-Instruct | Qwen3-VL text backbone | 36 层文本主干 |
| MoT | VLM KV Cache ↔ DiT layer-wise attention | 非普通 MLP Connector |
| NERO Proprioception 8D | 7 joints + gripper | 实际机器人状态接口 |
| XR-1 DiT + Flow Matching | 36 层 DiT + 5-step Euler sampling | 生成连续动作块 |
| XR-1 UMI pre-training | 官方基础模型预训练 | 100K+ 小时，不是本地 NERO 数据 |
| Cross-embodiment post-training | 官方本体/指令对齐 | 不等同于 NERO 下游微调 |
| NERO downstream fine-tuning | 本地 M3/M4/EF4/M5 | 任务适配与实验机制 |

## 5. 不要混淆的五件事

1. **Qwen3-VL Vision Tower 与 Text Backbone**：乐高分开摆放只是教学拆分，真实 Qwen3-VL 是集成多模态模型。
2. **MoT 与 Linear Connector**：MoT 是逐层 KV Cache 交互，不是一个简单投影层。
3. **DiT 与 Flow Matching**：DiT 是网络，Flow Matching 是训练/采样机制。
4. **XR-1 60D 与 NERO 8D**：60D 是基础模型内部容器；NERO 实际状态和物理命令接口为 8D。
5. **M4 与 M5**：M4 合并中间步骤语义但不硬停；M5 学习边界、截断动作块并等待人工确认。

## 6. 主要来源

- [Xiaomi-Robotics-1 官方技术介绍](https://robotics.xiaomi.com/xiaomi-robotics-1.html)
- [Xiaomi-Robotics-1 官方 GitHub](https://github.com/XiaomiRobotics/Xiaomi-Robotics-1)
- [官方 XR1.py](https://github.com/XiaomiRobotics/Xiaomi-Robotics-1/blob/main/xr1/mibot/models/VLA/XR1.py)
- [官方 Qwen3VL 实现](https://github.com/XiaomiRobotics/Xiaomi-Robotics-1/blob/main/xr1/mibot/models/VLM/qwen3vl.py)
- [Qwen3-VL-4B-Instruct config.json](https://huggingface.co/Qwen/Qwen3-VL-4B-Instruct/blob/main/config.json)
- [NERO 本地模型演化与机制记录](https://github.com/kayn6554-creator/nero-xr1-experiments/blob/main/docs/model-evolution-and-mechanisms.md)
- [NERO 推理 Client](https://github.com/kayn6554-creator/nero-xr1-experiments/blob/main/code/collector/nero_vla_client.py)
- [NERO M3 数据配置](https://github.com/kayn6554-creator/nero-xr1-experiments/blob/main/code/xr1-overlay/configs/data/nero3_m3_20261110.yaml)
- [NERO M5 数据配置](https://github.com/kayn6554-creator/nero-xr1-experiments/blob/main/code/xr1-overlay/configs/data/nero3_m5sb_20261112.yaml)
