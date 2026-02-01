# 事实核查自改进系统

基于大语言模型(LLM)的事实核查系统，具有**自我改进**能力。系统通过Generator-Reflector-Curator三阶段循环，能够从人类反馈中学习并动态更新规则库。

## 🌟 核心创新

- **动态规则库(Playbook)**: 从5条初始规则逐步演化
- **自改进循环**: Generator → Reflector → Curator → 规则更新
- **完整可解释性**: 每次判断都记录使用的规则ID
- **版本控制**: 规则库演化过程完整可追溯

## 📁 项目结构

```
fact_check_system/
├── config/                 # 配置模块
│   ├── __init__.py
│   └── settings.py
├── data/                   # 数据存储
│   ├── playbook/          # 规则库
│   ├── cases/             # 案例日志
│   └── feedback/          # 反馈记录
├── agents/                # 三个核心Agent
│   ├── generator.py       # AgentA: 事实核查生成器
│   ├── reflector.py       # AgentB: 反思器
│   └── curator.py         # AgentC: 整编器
├── tools/                 # 工具模块
│   ├── search_tool.py     # 网络搜索
│   └── playbook_tool.py   # Playbook操作
├── prompts/               # Prompt模板
├── schemas/               # 数据模型
│   ├── playbook.py        # 规则库数据结构
│   ├── verdict.py         # 裁决输出结构
│   └── feedback.py        # 反馈结构
├── utils/                 # 工具函数
│   ├── playbook_manager.py
│   └── logger.py
├── main.py                # 主程序
├── demo.py                # 快速演示
└── requirements.txt
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目（或创建目录）
mkdir fact_check_system
cd fact_check_system

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置API密钥

创建 `.env` 文件：

```bash
# 必需：Google Gemini API
GOOGLE_API_KEY=your_google_api_key_here

# 可选：模型选择（默认使用gemini-2.0-flash-exp）
GEMINI_MODEL=gemini-2.0-flash-exp

# 可选：搜索API（不配置将使用模拟搜索）
SERPAPI_KEY=your_serpapi_key_here
```

**获取API密钥:**
- Google Gemini: https://makersuite.google.com/app/apikey
- SerpAPI (可选): https://serpapi.com/

### 3. 运行演示

```bash
# 快速演示（推荐首次运行）
python demo.py

# 完整交互式程序
python main.py
```

## 📖 使用说明

### Demo模式

```bash
python demo.py
```

选择：
- **选项1 - 简单演示**: 运行一个完整的自改进循环
- **选项2 - 批量演示**: 运行3个案例，观察规则库演化

### 完整模式

```bash
python main.py
```

选择：
- **选项1 - 交互模式**: 手动输入待核查信息并提供反馈
- **选项2 - 批量模式**: 自动运行预设案例

## 🔄 工作流程

```
1. [输入] 待核查信息
   ↓
2. [AgentA Generator] 
   - 提取声明
   - 检索证据（可调用搜索工具）
   - 生成裁决 + 详细日志
   ↓
3. [人类反馈]
   - 标注正确答案
   - 标注反馈类型
   ↓
4. [AgentB Reflector]
   - 对比分析
   - 诊断错误原因
   - 提炼关键洞见
   ↓
5. [AgentC Curator]
   - 将洞见转化为规则更新
   - 生成Delta增量
   ↓
6. [Playbook更新]
   - 应用增量更新
   - 保存历史版本
   ↓
7. [循环] 使用更新后的规则库处理下一个案例
```

## 📊 规则库演化示例

```
初始状态 (v1.0):
- 5条元规则
- 准确率: ~60%

迭代3次后 (v1.3):
- 8-10条规则
- 准确率: ~75%

迭代10次后 (v1.10):
- 15+条规则
- 准确率: >85%
```

## 🔧 高级配置

### 自定义测试案例

编辑 `main.py` 中的 `test_cases` 列表：

```python
test_cases = [
    "你的自定义待核查信息1",
    "你的自定义待核查信息2",
    # ...
]
```

### 调整模型参数

编辑 `config/settings.py`:

```python
TEMPERATURE = 0.1       # 降低温度提高稳定性
MAX_TOKENS = 4096       # 调整输出长度
```

### 查看规则库演化

```bash
# 查看当前规则库
cat data/playbook/current.json

# 查看历史版本
ls data/playbook/history/

# 查看案例日志
ls data/cases/
```

## 📈 验证指标

系统成功运行的标志：

- ✅ Playbook规则数从5条增长到15+条
- ✅ 每条新规则都有`created_from`字段（可追溯来源）
- ✅ 历史版本完整保存在`history/`目录
- ✅ 裁决输出包含`used_rules`（展示使用了哪些规则）
- ✅ 准确率随迭代次数提升

## ⚠️ 常见问题

### Q: API调用失败

**检查:**
1. `.env`文件中的`GOOGLE_API_KEY`是否正确
2. API密钥是否有足够的配额
3. 网络连接是否正常

### Q: JSON解析错误

**原因:** Gemini模型输出格式不稳定

**解决:** 系统已内置容错机制，会自动使用默认值

### Q: 搜索功能不可用

**正常情况:** 如果未配置搜索API，系统会使用模拟搜索（demo用）

**配置真实搜索:** 在`.env`中添加`SERPAPI_KEY`

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 License

MIT License

## 📮 联系

如有问题请提交Issue
