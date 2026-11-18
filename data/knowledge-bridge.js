window.KNOWLEDGE_BRIDGE = {
  "version": 1,
  "links": [
    {
      "nodeId": "qwen3_vl_4b",
      "targetType": "brick",
      "targetId": "qwen3vl_processor",
      "label": "AutoProcessor / tokenizer",
      "relation": "preprocessing"
    },
    {
      "nodeId": "qwen3_vl_4b",
      "targetType": "brick",
      "targetId": "qwen3vl_vision",
      "label": "Vision Tower",
      "relation": "model_component"
    },
    {
      "nodeId": "qwen3_vl_4b",
      "targetType": "brick",
      "targetId": "qwen3vl_backbone",
      "label": "Qwen3-VL text backbone",
      "relation": "model_component"
    },
    {
      "nodeId": "xr1_mot",
      "targetType": "brick",
      "targetId": "xr1_mot",
      "label": "MoT / layer-wise KV Cache",
      "relation": "same_component"
    },
    {
      "nodeId": "xr1_dit",
      "targetType": "brick",
      "targetId": "xr1_dit_flow",
      "label": "DiT action expert",
      "relation": "same_component"
    },
    {
      "nodeId": "xr1_flow_matching",
      "targetType": "brick",
      "targetId": "xr1_dit_flow",
      "label": "Flow Matching generation",
      "relation": "method_of"
    },
    {
      "nodeId": "xiaomi_robotics_1",
      "targetType": "preset",
      "targetId": "nero_xr1",
      "label": "以 XR-1 为基础的 NERO 模型预设",
      "relation": "base_model",
      "version": "M3"
    },
    {
      "nodeId": "nero_xr1_project",
      "targetType": "preset",
      "targetId": "nero_xr1",
      "label": "打开 NERO × XR-1 模型预设",
      "relation": "project_instance",
      "version": "M3"
    },
    {
      "nodeId": "nero_merge23",
      "targetType": "version",
      "targetId": "M4",
      "label": "打开 M4 / Merge23",
      "relation": "experiment_variant",
      "version": "M4"
    },
    {
      "nodeId": "nero_ee_action",
      "targetType": "version",
      "targetId": "EF4",
      "label": "打开 EF4 / EE + IK",
      "relation": "experiment_variant",
      "version": "EF4"
    },
    {
      "nodeId": "nero_step_flag",
      "targetType": "version",
      "targetId": "M5",
      "label": "打开 M5 / Step Flag",
      "relation": "experiment_variant",
      "version": "M5"
    }
  ]
};
