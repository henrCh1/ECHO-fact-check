# ECHO - Fact Checking

<div align="center">

![Version](https://img.shields.io/badge/version-2.0.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

**An AI-Powered Fact-Checking System with Self-Evolving Rule Base**

[English](README.md) | [中文](README_CN.md)

</div>

---

## Changelog

### v2.0.0

- Added a human-in-the-loop evolution workflow with a `PendingBuffer` that batches 3 evolving-mode cases before requesting feedback.
- Introduced dual rule status labels: `Verified` for trusted rules and `Trial` for feedback-generated rules that remain visible in prompts and UI.
- Added batched review APIs and frontend review modal so users can mark verdict correctness and reasoning correctness for buffered cases.
- Rewired evolving mode to buffer cases first and run supervised `WarmupReflector -> Curator -> apply_update` only after user feedback is submitted.
- Exposed `Trial/Verified` rule badges in the playbook and result pages.
- Improved Gemini compatibility by normalizing non-string `response.content` payloads returned by newer Gemini models.
- Added explicit execution-time grounding to prompts so recent claims are judged against the runtime date instead of the model's assumed year.
- Added frontend runtime settings for Gemini API Key and model name, backed by a new `/api/settings` endpoint that persists to `.env`.
- Changed the default Gemini model to `gemini-3-flash-preview`.
- Upgraded the public system version from `1.0.0` to `2.0.0`.

## 📖 Overview

ECHO is an advanced fact-checking system that combines Large Language Models (LLMs) with an evolving rule-based memory system. Unlike traditional fact-checkers, ECHO learns from each verification, continuously improving its detection capabilities through supervised and self-reflection mechanisms.

### ✨ Key Features

- 🧠 **Dual Memory Architecture**: Separate Detection Memory (for false claims) and Trust Memory (for verified truths)
- 🔄 **Self-Evolving Rules**: System learns and generates new rules from verification experience
- 🤖 **Multi-Agent Pipeline**: Specialized agents for planning, investigation, and judgment
- 🎯 **Warmup Learning**: Pre-train on labeled datasets to bootstrap the rule base
- 🌐 **Web Interface**: Modern React-based frontend for easy interaction
- 📊 **Real-time Progress**: Step-by-step verification progress tracking
- 📚 **Rule Transparency**: Expandable rule details with full IF-THEN logic

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ECHO System                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐          │
│  │  Generator  │───▶│  Reflector  │───▶│   Curator   │          │
│  │   Agent     │    │    Agent    │    │    Agent    │          │
│  └─────────────┘    └─────────────┘    └─────────────┘          │
│         │                  │                  │                  │
│         ▼                  ▼                  ▼                  │
│  ┌─────────────────────────────────────────────────┐            │
│  │              Playbook (Rule Base)                │            │
│  │  ┌─────────────────┐  ┌─────────────────┐       │            │
│  │  │Detection Memory │  │  Trust Memory   │       │            │
│  │  │(False patterns) │  │(Truth patterns) │       │            │
│  │  └─────────────────┘  └─────────────────┘       │            │
│  └─────────────────────────────────────────────────┘            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Core Agents

| Agent | Role | Description |
|-------|------|-------------|
| **Generator** | Fact-Checker | Executes verification using Planner→Investigator→Judge pipeline |
| **Reflector** | Self-Reflection | Analyzes verification results and generates insights |
| **Curator** | Rule Manager | Creates, updates, and manages rules based on insights |

### Verification Pipeline (Generator Agent)

1. **Planner**: Extracts claims, selects relevant rules, generates search strategies
2. **Investigator**: Executes searches, gathers evidence, assesses credibility
3. **Judge**: Synthesizes evidence, applies rules, renders final verdict

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for web interface)
- Google API Key (for Gemini LLM)

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/ECHO-fact-checking.git
cd ECHO-fact-checking

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: .\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements_all_branches.txt

# Configure environment
cp .env.template .env
# Edit .env and add your GOOGLE_API_KEY
```

### Configuration

Create a `.env` file with the following:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-3-flash-preview
```

---

## 💻 Usage

### Web Application (Recommended)

**One-Click Launch:**

```powershell
# Windows PowerShell (Recommended)
.\start.ps1

# Windows CMD
.\start.bat
```

**Access Points:**
- Frontend: http://localhost:3000
- API Documentation: http://localhost:8000/docs

### Command Line Interface

**Single Claim Verification:**

```bash
# Interactive mode
python single_check.py

# Direct verification
python single_check.py --claim "Company X declared bankruptcy in January 2026"
```

**Warmup Training:**

Train the system on a labeled dataset to bootstrap rules:

```bash
python -m warmup.warmup_main
```

The warmup dataset should be a CSV with columns:
- `Statement`: The claim text
- `Rating`: True/False label
- `Full_Analysis`: Ground truth analysis

**Benchmark Evaluation:**

```bash
python benchmark_main.py --dataset data/test_dataset.csv
```

---

## 🌐 Web Interface Features

### 🏠 Home Page
- Single claim input with mode selection (Static/Evolving)
- **Real-time progress indicator** with step tracking:
  - 提取关键声明 (Extract Claims)
  - 搜集证据 (Gather Evidence)
  - 分析判断 (Analyze & Judge)
  - 生成报告 (Generate Report)
  - 规则演化 (Rule Evolution - Evolving mode only)
- Batch CSV upload with drag-and-drop

### 📊 Result Page
- Detailed verdict with confidence score
- Evidence display with credibility ratings
- AI reasoning explanation
- **Expandable rule details** - Click any rule to view:
  - Rule type and memory type
  - Full description
  - IF-THEN condition and action
  - Confidence and evidence count
- Investigation process trace

### 📚 History Page
- Searchable verification history
- Filter by verdict, mode, confidence
- Delete functionality

### 📖 Playbook Page
- Detection and Trust memory tabs
- Rule browsing with metrics
- Playbook version tracking

### 📈 Statistics Dashboard
- Total verifications count
- True/False distribution chart
- Mode usage analytics
- Average confidence metrics

---

## 🔌 API Reference

### Verification Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/verify` | Verify single claim |
| POST | `/api/verify/batch` | Upload CSV for batch verification |
| GET | `/api/verify/batch/{task_id}` | Get batch task status |
| GET | `/api/verify/batch/{task_id}/download` | Download batch results |

### History Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/history` | List verification history |
| GET | `/api/history/{case_id}` | Get verification details |
| DELETE | `/api/history/{case_id}` | Delete history record |

### Playbook Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/playbook` | Get playbook status |
| GET | `/api/playbook/rules` | List all rules |
| GET | `/api/playbook/rules/{rule_id}` | Get rule details |
| POST | `/api/playbook/switch` | Switch active playbook |

### Warmup Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/warmup/upload` | Upload warmup dataset |
| POST | `/api/warmup/start` | Start warmup training |
| GET | `/api/warmup/{task_id}` | Get warmup status |

---

## 🎯 Verification Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Static** | Uses existing rules only | Fast verification, production use |
| **Evolving** | Triggers rule evolution after verification | Learning mode, improves over time |

---

## 📁 Project Structure

```
ECHO-fact-checking/
├── agents/                 # Core AI agents
│   ├── generator.py       # Main verification agent
│   ├── reflector.py       # Self-reflection agent
│   └── curator.py         # Rule curation agent
├── warmup/                 # Warmup training system
│   ├── warmup_main.py     # Warmup entry point
│   └── agents/            # Warmup-specific agents
├── api/                    # FastAPI backend
│   ├── main.py            # API entry point
│   ├── routers/           # API endpoints
│   ├── services/          # Business logic
│   └── schemas/           # Pydantic models
├── app/                    # React frontend
│   ├── pages/             # Page components
│   ├── components/        # UI components
│   └── services/          # API client
├── utils/                  # Utilities
│   └── playbook_manager.py # Rule base management
├── schemas/                # Pydantic data models
├── prompts/                # LLM prompt templates
├── config/                 # Configuration
├── data/                   # Data directory
│   └── playbook/          # Rule base storage
├── single_check.py        # Single claim verification CLI
├── benchmark_main.py      # Batch evaluation script
├── start.ps1              # PowerShell startup script
└── start.bat              # Windows batch startup script
```

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI
- **LLM**: Google Gemini (langchain-google-genai)
- **Data Validation**: Pydantic
- **Search**: Google Search API / SerpAPI

### Frontend
- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite 6
- **Styling**: Custom CSS utilities
- **Charts**: Recharts
- **Icons**: Lucide React
- **Routing**: React Router DOM

---

## 📝 Rule Base Format

Rules are stored as IF-THEN conditions:

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

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Google Gemini for LLM capabilities
- LangChain for AI orchestration framework
- The open-source fact-checking research community

---

<div align="center">

**Built with ❤️ for truth in the age of misinformation**

[⬆ Back to Top](#echo---evolving-cognitive-hierarchy-for-observation)

</div>
