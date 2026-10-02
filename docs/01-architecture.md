# Listing 文案师 — 业务架构

## 四层视图

```mermaid
flowchart TD
    subgraph L1["① 用户层"]
        U["月上新频繁、标题 SEO 靠抄的一人店"]
    end

    subgraph L2["② 数字员工层"]
        E["Listing 文案师<br/>①视觉员工的配套另一半——图和文案是同一次上架的两半"]
    end

    subgraph L3["③ 工作流层（5 条）"]
        W1["关键词挖掘与标题组合"]
        WN["…共 5 条"]
    end

    subgraph L4["④ 原子技能层（5 个）"]
        SK1["关键词组合"]
        SK2["卖点文案"]
        SK3["广告法合规预审"]
        SK4["转化结构模板"]
        SK5["A/B 文案变体"]
    end

    U -->|"提出需求"| E
    E -->|"编排调用"| W1
    W1 --> WN
    W1 --> SK1

    style L1 fill:#E8F4FD,stroke:#1976D2,color:#0D47A1
    style L2 fill:#FFF3E0,stroke:#E65100,color:#BF360C
    style L3 fill:#F3E5F5,stroke:#7B1FA2,color:#4A148C
    style L4 fill:#E8F5E9,stroke:#388E3C,color:#1B5E20
```

## 资产形态说明

本资产包为**纯提示词客户端资产**：

| 特性 | 说明 |
|------|------|
| 无运行时依赖 | 不调用任何模型 API，不需要 API Key |
| 平台无关 | 提示词为纯文本，可导入任意主流 AI 平台 |
| 用户自备算力 | 模型由用户自己的订阅提供 |
| 零服务端成本 | 资产方不产生任何调用费用 |

## 数据流

```mermaid
flowchart LR
    A["用户输入"] --> B["选择技能<br/>（粘贴 prompt.txt）"]
    B --> C["AI 按提示词处理"]
    C --> D["合规自检"]
    D --> E["人工审核"]
    E --> F["交付使用"]

    style D fill:#FFEBEE,stroke:#C62828,color:#B71C1C
    style E fill:#FFF9C4,stroke:#F9A825,color:#F57F17
```

> **关键设计**：所有对外输出必须经过「合规自检 → 人工审核」双闸门。

## 能力边界

| 维度 | 内容 |
|------|------|
| **目标用户** | 月上新频繁、标题 SEO 靠抄的一人店 |
| **做** | 标题组合、卖点、详情页文案、合规扫描 |
| **不做** | 不做：虚假功效宣称、极限词擦边 |
| **KPI** | 标题生成→上架 ≤10 分钟；合规扫描覆盖率 100%；CTR 环比提升 |
| **定价** | 30-80 元/月（单独卖偏弱，建议与①捆绑） |

---

*本图由 build_p0_assets.py 自动生成*
