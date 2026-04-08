# SparkGuardian 系统架构图

```mermaid
flowchart LR
    U[用户/老人/家属] --> UI[OpenClaw 对话界面]

    subgraph DGX[NVIDIA DGX Spark 本地推理节点]
        LLM[Qwen 32B NVFP4]
        VLLM[vLLM 推理服务\nOpenAI-compatible API]
        UI --> AGENT[OpenClaw Agent]
        AGENT --> VLLM
        VLLM --> LLM
        LLM --> VLLM
        VLLM --> AGENT
    end

    AGENT --> HAAPI[Home Assistant API]

    subgraph HOME[家庭设备中枢]
        HA[Home Assistant]
        DEV[智能电器实体\n灯/空调/传感器/开关]
        HIST[历史状态数据\n活动/用电/环境]
        HAAPI --> HA
        HA <--> DEV
        HA --> HIST
    end

    AGENT --> ANALYSIS[行为分析与风险判断]
    ANALYSIS --> WARN[安全告警与建议]
    WARN --> ACT[联动处置\n设备调整/关闭]
    ACT --> HAAPI
    WARN --> NOTICE[家属通知]
```

## 数据流说明

1. 用户通过 OpenClaw 发起自然语言请求（控制或查询）。  
2. OpenClaw Agent 调用本地 Qwen 32B NVFP4（经 vLLM）进行意图理解与决策。  
3. Agent 通过 Home Assistant API 执行设备控制、读取实时与历史状态。  
4. 行为分析模块结合历史数据输出风险等级、解释依据和处置建议。  
5. 系统执行联动动作，并向用户/家属返回结果与提醒。

## 架构价值

- 本地推理：核心家庭数据不依赖云端大模型。
- 可解释闭环：从“查询/控制”扩展到“分析/预警/处置”。
- 场景导向：面向独居老人安全，兼顾实用性与可落地性。
