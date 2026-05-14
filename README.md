# 🗺️ NaviDoc

NaviDoc is a lightweight, **completely local, zero-API, tree-based RAG framework** designed to navigate document structures intelligently. Instead of blindly chopping your files into vector chunks, NaviDoc maps your documents into a logical structural tree hierarchy and uses local LLMs to precisely steer and navigate to answers.

[![License: MIT](https://shields.io)](https://opensource.org)
[![Python 3.10+](https://shields.io)](https://python.org)
[![Ollama Native](https://shields.io)](https://ollama.com)

---

## ✨ Features

*   **🔒 100% Private & Offline:** Your documents never leave your machine. Zero cloud APIs, zero telemetry.
*   **🪙 Zero Token Costs:** Powered entirely by open-weights models running locally on your hardware.
*   **🌳 Tree-Based Navigation:** Mimics human navigation by following document headers (`#`, `##`) instead of standard proximity vector chunks.
*   **⚡ High Precision:** Pinpoints specific structural sections, avoiding context contamination or context blowouts.

---

## 🚀 Getting Started

### 1. Prerequisites

First, ensure you have **Ollama** installed on your system to host your local LLM engine.

1. Download Ollama from [ollama.com](https://ollama.com).
2. Pull your local LLM of choice (e.g., Llama 3 or Mistral) via your terminal:
   ```bash
   ollama pull llama3
   ```

### 2. Installation

Clone this repository and install the minimal, lightweight dependency package:

```bash
git clone github.com
cd navidoc
pip install ollama
```

### 3. Usage Example

Save your project script as `navidoc.py` and execute it. Here is how simple it is to parse and query a document:

```python
from navidoc import NaviDoc

# Initialize NaviDoc using your local Ollama model
engine = NaviDoc(model="llama3")

# Ingest and structurally index any local markdown document
status = engine.ingest_markdown("your_document.md")
print(status)

# Query your document offline with 0.0 temperature precision
response = engine.query("What are the exact system requirements?")
print(response)
```

---

## 🛠️ Architecture Blueprint

NaviDoc runs by organizing document content into key-value trees where headers map directly to contextual section blocks:

```text
📄 your_document.md ──► 🌳 Tree Mapping ──► 🧠 Local LLM Navigation
                         ├── # Header 1          ├── Checks Section 1 -> SKIP
                         └── # Header 2          └── Checks Section 2 -> MATCH 🎯
```

---

## 📜 License

NaviDoc is open-source software distributed completely free under the **[MIT License](LICENSE)**. Feel free to modify, distribute, and adapt it for personal or commercial workflows.
