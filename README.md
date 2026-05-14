# 🗺️ NaviDoc: The Ultimate Local RAG Framework

[![PyPI Version](https://img.shields.io/pypi/v/navidoc.svg)](https://pypi.org/project/navidoc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**NaviDoc** is a lightweight, **completely local, zero-API, tree-based RAG (Retrieval-Augmented Generation) framework** designed to navigate document structures with human-like intelligence. 

Stop blindly chopping your documents into arbitrary flat chunks. NaviDoc maps your files into a logical structural tree hierarchy and uses local LLMs or ultra-fast static embeddings to precisely steer and navigate to answers.

---

## 🚀 Why NaviDoc is Different (The "Crazy" Features)

### 🧠 1. Intelligent "Vectorless" Tree Navigation
*   **🌳 True Hierarchy**: NaviDoc mimics human reading. It follows headers, font sizes, and sections to build a mental map of your document.
*   **🛡️ Dead-End Protection**: Our smart navigation algorithm includes LLM verification. If it navigates to a section that turns out to be irrelevant, it falls back to parent content rather than giving a hallucinated answer!

### ⚡ 2. Blazing Fast Hybrid Mode
*   **🚀 Model2Vec Integration**: Use the cutting-edge `potion-base-32M` model for lightning-fast tree navigation instead of heavy LLM calls. Up to **500x faster** on CPU!
*   **📉 History Limit Control**: Configurable chat history limits (`max_history`) to prevent context blowouts and keep your local LLM fast and responsive.
*   **🗜️ Context Compression**: Auto-summarizes large sections using pure Python (no LLM load) to prevent context overflow!
*   **🤖 Qwen 2.5 (1.5B) by Default**: Uses the ultra-smart and efficient `qwen2.5:1.5b` model as the default LLM for fast responses on any hardware!

### 📄 3. Enterprise Document Support



*   **Multi-Format Mastery**: Native support for **Markdown**, **PDF** (with advanced font-size analysis), **DOCX** (with style detection), and **PPTX**.
*   **🖼️ OCR Weaponry**: Ingest images (`.png`, `.jpg`, `.jpeg`) via seamless **GLM-OCR** integration!
*   **🗄️ Auto-Scaling SQLite Tree**: Support for massive files! If a file is larger than **10MB**, NaviDoc automatically switches to a self-referencing SQLite tree structure to save memory!

### 🔒 4. 100% Privacy & Zero Cost
*   **🔒 100% Private**: Your documents never leave your machine. Zero cloud APIs, zero telemetry, zero data leaks.
*   **💬 Persistent Chat Memory**: Backed by a localized SQLite database to maintain conversation memory across sessions (SDK-style).

### 🌐 5. Visual Web Interface (NEW!)
*   **🌐 Local Web UI**: Launch a beautiful, premium web interface to chat with your documents using `navidoc ui` (accessible at `http://127.0.0.1:7860` by default)! (Powered by Gradio).
*   **⚙️ Configurable Port**: Change the port by setting the `NAVIDOC_PORT` environment variable (e.g., `NAVIDOC_PORT=8080 navidoc ui`).



---


## 🛠️ Installation

NaviDoc comes with **all batteries included**! Core dependencies like Model2Vec, Sentence-Transformers, and GLM-OCR are installed automatically!

### Using `pip`:
```bash
pip install navidoc
```

### Using `uv` (Highly Recommended):
```bash
uv add navidoc
```

---

## ⌨️ Master the CLI

NaviDoc comes with a powerful CLI that acts as a bridge between you and your local AI environment:

| Command | Description |
| :--- | :--- |
| `navidoc install-ollama` | Auto-downloads and installs Ollama for your OS (Windows/Linux). |
| `navidoc doctor` | Checks the status of all dependencies (Ollama, Model2Vec, OCR). |
| `navidoc run <model>` | Directly run an Ollama model. |
| `navidoc pull <model>` | Pull a model from the Ollama library. |
| `navidoc list` | List all installed Ollama models. |
| `navidoc ollama <args>` | Forward any command directly to the Ollama service. |

*If using `uv`, you can run any command directly without installing globally:*
```bash
uv run navidoc doctor
```

---

## 💻 Quick Start (Code Examples)

### 1. Basic Ingestion & Query

```python
from navidoc import NaviDoc

# Initialize (Defaults to 'phi3' model)
engine = NaviDoc()

# For ultra-fast navigation using Model2Vec embeddings
# engine = NaviDoc(use_embeddings=True)

# Ingest a document (Auto-detects format)
engine.ingest("enterprise_guide.pdf")

# Query your document offline
response = engine.query("What are the exact system requirements?")
print(response)
```

### 2. Multi-Turn Persistent Chat (SDK Style)

NaviDoc remembers conversations across sessions using a local SQLite database!

```python
from navidoc import NaviDoc

# Initialize with a specific session ID
engine = NaviDoc(session_id="project_alpha_chat")

engine.ingest("project_plan.docx")

# First turn
print(engine.chat("Who is the project manager?"))

# Second turn (maintains history)
print(engine.chat("What are their primary responsibilities?"))
```

---

## 🤝 Contributing & Open Source

We are building the future of local, private document understanding and we want your help! Whether you want to add new parsers, optimize the tree navigation, or improve the docs — all contributions are welcome.

*   **PyPI**: [https://pypi.org/project/navidoc/](https://pypi.org/project/navidoc/)
*   **GitHub**: [https://github.com/Bishwajitgarai/navidoc](https://github.com/Bishwajitgarai/navidoc)

Feel free to open issues or submit PRs on our GitHub Repository! 🚀
