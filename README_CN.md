# ECHO - 事实核查

<div align="center">

![版本](https://img.shields.io/badge/版本-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![许可证](https://img.shields.io/badge/许可证-MIT-orange)

**具有自演化规则库的 AI 驱动事实核查系统**

[English](README.md) | [中文](README_CN.md)

</div>

---

## 📖 概述

ECHO 是一个先进的事实核查系统，将大型语言模型（LLM）与演化的规则记忆系统相结合。与传统事实核查工具不同，ECHO 能够从每次验证中学习，通过监督和自我反思机制持续提升检测能力。

### ✨ 核心特性

- 🧠 **双记忆架构**：分离的检测记忆（针对虚假声明）和信任记忆（针对已验证事实）
- 🔄 **自演化规则**：系统从验证经验中学习并生成新规则
- 🤖 **多智能体流水线**：专门的规划、调查和裁决智能体
- 🎯 **预热学习**：在标注数据集上预训练以初始化规则库
- 🌐 **Web 界面**：基于 React 的现代化前端交互
- 📊 **实时进度**：分步骤的验证进度追踪
- 📚 **规则透明**：可展开的规则详情，显示完整的 IF-THEN 逻辑

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                         ECHO 系统                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  生成器     │───▶│  反思器     │───▶│   策展器    │          │
│  │  Generator  │    │  Reflector  │    │   Curator   │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌─────────────────────────────────────────────────┐            │
│  │              规则库 (Playbook)                   │            │
│  │  ┌─────────────────┐  ┌─────────────────┐       │            │
│  │  │   检测记忆      │  │   信任记忆      │       │            │
│  │  │(虚假模式识别)   │  │(真实模式识别)   │       │            │
│  │  └─────────────────┘  └─────────────────┘       │            │
│  └─────────────────────────────────────────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 核心智能体

| 智能体 | 角色 | 描述 |
|-------|------|-------------|
| **Generator（生成器）** | 事实核查 | 使用 规划器→调查员→裁判 流水线执行验证 |
| **Reflector（反思器）** | 自我反思 | 分析验证结果并生成洞察 |
| **Curator（策展器）** | 规则管理 | 基于洞察创建、更新和管理规则 |

### 验证流水线（生成器智能体）

1. **Planner（规划器）**：提取声明、选择相关规则、生成搜索策略
2. **Investigator（调查员）**：执行搜索、收集证据、评估可信度
3. **Judge（裁判）**：综合证据、应用规则、做出最终判定

---

## 🚀 快速开始

### 前置要求

- Python 3.10+
- Node.js 18+（用于 Web 界面）
- Google API 密钥（用于 Gemini LLM）

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/ECHO-fact-checking.git
cd ECHO-fact-checking

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或: .\venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements_all_branches.txt

# 配置环境
cp .env.template .env
# 编辑 .env 文件并添加你的 GOOGLE_API_KEY
```

### 配置

创建 `.env` 文件，内容如下：

```env
GOOGLE_API_KEY=你的_gemini_api_密钥
GEMINI_MODEL=gemini-2.5-flash
```

---

## 💻 使用方法

### Web 应用（推荐）

**一键启动：**

```powershell
# Windows PowerShell（推荐）
.\start.ps1

# Windows CMD
.\start.bat
```

**访问地址：**
- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs

### 命令行界面

**单条声明验证：**

```bash
# 交互式模式
python single_check.py

# 直接验证
python single_check.py --claim "某公司在2026年1月宣布破产"
```

**预热训练：**

在标注数据集上训练系统以初始化规则库：

```bash
python -m warmup.warmup_main
```

预热数据集应为包含以下列的 CSV 文件：
- `Statement`：声明文本
- `Rating`：True/False 标签
- `Full_Analysis`：真实分析结果

**基准测试：**

```bash
python benchmark_main.py --dataset data/test_dataset.csv
```

---

## 🌐 Web 界面功能

### 🏠 主页
- 单条声明输入，支持模式选择（静态/演化）
- **实时进度指示器**，分步骤追踪：
  - 提取关键声明
  - 搜集证据
  - 分析判断
  - 生成报告
  - 规则演化（仅演化模式）
- 批量 CSV 上传，支持拖拽

### 📊 结果页面
- 详细判定结果及置信度分数
- 证据展示及可信度评级
- AI 推理过程说明
- **可展开的规则详情** - 点击任意规则查看：
  - 规则类型和记忆类型
  - 完整描述
  - IF-THEN 条件和动作
  - 置信度和证据数量
- 调查过程追踪

### 📚 历史记录页面
- 可搜索的验证历史
- 按判定结果、模式、置信度筛选
- 删除功能

### 📖 规则库页面
- 检测记忆和信任记忆标签页
- 规则浏览及指标展示
- 规则库版本追踪

### 📈 统计仪表板
- 总验证次数
- 真/假分布图表
- 模式使用分析
- 平均置信度指标

---

## 🔌 API 参考

### 验证端点

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| POST | `/api/verify` | 验证单条声明 |
| POST | `/api/verify/batch` | 上传 CSV 进行批量验证 |
| GET | `/api/verify/batch/{task_id}` | 获取批量任务状态 |
| GET | `/api/verify/batch/{task_id}/download` | 下载批量结果 |

### 历史记录端点

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/api/history` | 列出验证历史 |
| GET | `/api/history/{case_id}` | 获取验证详情 |
| DELETE | `/api/history/{case_id}` | 删除历史记录 |

### 规则库端点

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| GET | `/api/playbook` | 获取规则库状态 |
| GET | `/api/playbook/rules` | 列出所有规则 |
| GET | `/api/playbook/rules/{rule_id}` | 获取规则详情 |
| POST | `/api/playbook/switch` | 切换活动规则库 |

### 预热端点

| 方法 | 端点 | 描述 |
|--------|----------|-------------|
| POST | `/api/warmup/upload` | 上传预热数据集 |
| POST | `/api/warmup/start` | 开始预热训练 |
| GET | `/api/warmup/{task_id}` | 获取预热状态 |

---

## 🎯 验证模式

| 模式 | 描述 | 使用场景 |
|------|-------------|----------|
| **静态模式** | 仅使用现有规则 | 快速验证，生产环境使用 |
| **演化模式** | 验证后触发规则演化 | 学习模式，随时间改进 |

---

## 📁 项目结构

```
ECHO-fact-checking/
├── agents/                 # 核心 AI 智能体
│   ├── generator.py       # 主验证智能体
│   ├── reflector.py       # 自我反思智能体
│   └── curator.py         # 规则策展智能体
├── warmup/                 # 预热训练系统
│   ├── warmup_main.py     # 预热入口
│   └── agents/            # 预热专用智能体
├── api/                    # FastAPI 后端
│   ├── main.py            # API 入口
│   ├── routers/           # API 端点
│   ├── services/          # 业务逻辑
│   └── schemas/           # Pydantic 模型
├── app/                    # React 前端
│   ├── pages/             # 页面组件
│   ├── components/        # UI 组件
│   └── services/          # API 客户端
├── utils/                  # 工具函数
│   └── playbook_manager.py # 规则库管理
├── schemas/                # Pydantic 数据模型
├── prompts/                # LLM 提示词模板
├── config/                 # 配置
├── data/                   # 数据目录
│   └── playbook/          # 规则库存储
├── single_check.py        # 单条声明验证 CLI
├── benchmark_main.py      # 批量评估脚本
├── start.ps1              # PowerShell 启动脚本
└── start.bat              # Windows 批处理启动脚本
```

---

## 🛠️ 技术栈

### 后端
- **框架**：FastAPI
- **LLM**：Google Gemini (langchain-google-genai)
- **数据验证**：Pydantic
- **搜索**：Google Search API / SerpAPI

### 前端
- **框架**：React 19 + TypeScript
- **构建工具**：Vite 6
- **样式**：自定义 CSS 工具类
- **图表**：Recharts
- **图标**：Lucide React
- **路由**：React Router DOM

---

## 📝 规则库格式

规则以 IF-THEN 条件形式存储：

```json
{
  "rule_id": "det-00123",
  "type": "strategy",
  "condition": "IF claim_contains=financial_data AND source_type=social_media",
  "action": "Cross-verify with official financial databases",
  "confidence": 0.85,
  "evidence_count": 23,
  "memory_type": "detection"
}
```

---

## 🤝 贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- Google Gemini 提供 LLM 能力
- LangChain 提供 AI 编排框架
- 开源事实核查研究社区

---

<div align="center">

**在错误信息泛滥的时代，用 ❤️ 为真相而构建**

[⬆ 返回顶部](#echo---演化认知层级观察系统)

</div>
