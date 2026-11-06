# 配置说明：怎么加一篇新论文

所有内容都在 `index.html` 顶部的 `<script type="application/json" id="lego-config">` 里，分四块：

| 字段 | 作用 |
| --- | --- |
| `slots` | 插槽定义。一般不用改，除非要加新的插槽类型 |
| `bricks` | 积木（组件），每块对应一篇论文或一个模块 |
| `presets` | 预设模型，决定「一键拼装」和「这是 xxx！」的识别 |
| `evolution` | 演化路线依次播放的预设 id |

改完运行一次检查：

```bash
python3 tools/validate_config.py
```

它会指出缺字段、id 写错、积木放错槽、快捷键冲突这类问题。

## 插槽 id

| id | 名称 | 积木的 `cat`（决定颜色） |
| --- | --- | --- |
| `tokenizer` | 分词器 | `input` |
| `vision` | 视觉编码器 | `input` |
| `connector` | 模态连接器 | `connector` |
| `proprio` | 机器人状态（可选） | `input` |
| `backbone` | Transformer 主干型号 | `backbone` |
| `head` | 输出头 | 输出文字用 `text`，输出动作用 `action` |
| `recipe` | 训练配方（可多块） | `recipe` |
| `pos` | Block 内：位置编码 | `pos` |
| `norm` | Block 内：归一化 | `norm` |
| `attn` | Block 内：注意力 | `attn` |
| `ffn` | Block 内：前馈网络 | `ffn` |

## 加一块积木

```json
{
  "id": "my_attn",
  "slot": "attn",
  "cat": "attn",
  "name": "积木上的大字",
  "sub": "积木上的小字，可省略",
  "paper": "论文标题",
  "year": "2025",
  "org": "机构",
  "idea": "一句话核心思想",
  "solves": "它替换了什么 / 解决了什么问题",
  "metaphor": "生活化比喻",
  "flow": "数据流动画里这一步显示的说明，可省略",
  "inNote": "Block 展开页下方说明卡里的文字，Block 内积木才用，可省略",
  "links": [{"label": "arXiv:xxxx.xxxxx", "url": "https://arxiv.org/abs/xxxx.xxxxx"}],
  "verify": []
}
```

- `verify` 里写字段名（如 `["org", "links"]`），卡片上对应字段会显示「待核实」。都核实过就留空或删掉。
- 积木会自动出现在零件库对应分组里，不需要改别的地方。

几类积木的额外字段：

- **主干型号**（`slot: "backbone"`）必须带 `inner`，写这个模型 Block 内部四个槽的积木 id，插入主干时会自动填好。还可以加 `layers`（显示为「×N 层」）和 `note`。
  ```json
  "layers": "32", "inner": {"pos": "rope", "norm": "rmsnorm", "attn": "gqa", "ffn": "swiglu"}
  ```
- **连接器**如果会压缩 token 数量（像 Q-Former），加 `"reduce": true`，数据流动画里 patch 数会变少。
- **归一化**加 `"placement": "pre"` 或 `"post"`，决定 Block 展开图里它放在残差相加之前还是之后。

## 加一个预设模型

```json
{
  "id": "my_model",
  "hotkey": "",
  "name": "按钮和徽章上显示的名字",
  "kind": "VLA",
  "slots": {"tokenizer": "sp_bpe", "vision": "siglip", "connector": "mlp2", "proprio": null, "backbone": "gemma", "head": "flow_expert"},
  "inner": {"pos": "rope", "norm": "rmsnorm", "attn": "mqa", "ffn": "geglu"},
  "recipe": ["pretrain", "oxe"],
  "talk": ["讲解提示面板里的要点 1", "要点 2"],
  "evoNote": "放进演化路线时，这一步顶部显示的一句话"
}
```

- `slots` 六个键都要写，没有的写 `null`。
- `kind` 只能是 `LLM`、`VLM`、`VLA`，决定按钮颜色。
- `hotkey` 可选 `0`–`9`，目前都被占用了，新预设留空就只出现在按钮行里。
- 识别规则：
  - `ignore`：识别时跳过的槽，用于论文没写清楚的部分，例如 `["connector"]`。
  - `alt`：某个槽可接受的其他积木，例如 `{"vision": ["vit", "clip_vit"]}`。
- 想放进演化路线，就把 `id` 加到 `evolution` 数组里的合适位置。
