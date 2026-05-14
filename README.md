# 🗺️ NaviDoc

NaviDoc is a lightweight, **completely local, zero-API, tree-based RAG framework** designed to navigate document structures intelligently. Instead of blindly chopping your files into vector chunks, NaviDoc maps your documents into a logical structural tree hierarchy and uses local LLMs to precisely steer and navigate to answers.

🔗 **Links:**
*   **PyPI**: [https://pypi.org/project/navidoc/](https://pypi.org/project/navidoc/)
*   **GitHub**: [https://github.com/Bishwajitgarai/navidoc](https://github.com/Bishwajitgarai/navidoc)


---

## ✨ Features

*   **🔒 100% Private & Offline:** Your documents never leave your machine. Zero cloud APIs, zero telemetry.
*   **🌳 Tree-Based Navigation:** Mimics human navigation by following document structures (headers, font sizes) instead of standard proximity vector chunks.
*   **⚡ High Precision:** Pinpoints specific structural sections, avoiding context contamination or context blowouts.
*   **📄 Multi-Format Support**: Supports Markdown, PDF (with font-size analysis), DOCX (with style detection), and PPTX.
*   **💾 Index Persistence**: Save your indexed tree structures to JSON and reload them instantly.
*   **💬 Chat SDK**: Maintain conversation history with your documents SDK-style.

---

## 🚀 Getting Started

### 1. Prerequisites

NaviDoc requires **Ollama** to host your local LLM engine.

1.  Download and install Ollama from [ollama.com](https://ollama.com).
2.  Pull a smart, small model (we recommend `phi3` or `llama3`):
    ```bash
    ollama pull phi3
    ```
3.  Ensure the Ollama service is running in the background before running NaviDoc.

### 2. Installation

Install NaviDoc via pip:

```bash
pip install navidoc
```

Or using `uv`:

```bash
uv add navidoc
```

---

## 💡 Usage Examples

### 🔍 One-off Query
```python
from navidoc import NaviDoc

# Initialize (defaults to phi3 or NAVIDOC_MODEL_NAME env var)
engine = NaviDoc()

# Ingest and structurally index any local document
status = engine.ingest("your_document.pdf")
print(status)

# Query your document offline
response = engine.query("What are the exact system requirements?")
print(response)
```

### 💬 Multi-turn Chat (SDK Style)
```python
from navidoc import NaviDoc

engine = NaviDoc()
engine.ingest("manual.docx")

# First turn
print(engine.chat("How do I install the battery?"))

# Second turn (remembers context and history!)
print(engine.chat("Where can I buy a replacement?"))

# Clear history if needed
engine.clear_history()
```

### 💾 Save & Fast Load Index
Avoid re-parsing large documents by saving the tree index.
```python
from navidoc import NaviDoc

engine = NaviDoc()

# First time: Parse and Save
engine.ingest("massive_report.pdf")
engine.save_index("storage/indices/massive_report.json")

# Second time: Instant Load in milliseconds
engine.load_index("storage/indices/massive_report.json")
response = engine.query("What is the revenue?")
```

---

## ⚙️ Configuration

### Environment Variables
You can configure NaviDoc without changing your code by setting environment variables:

*   `NAVIDOC_MODEL_NAME`: Set the default Ollama model to use (Default: `phi3`).

**How to change it:**
*   **Windows (PowerShell)**: `$env:NAVIDOC_MODEL_NAME="llama3"`
*   **Linux/Mac**: `export NAVIDOC_MODEL_NAME="llama3"`

---

## 🧠 How Vectorless RAG Works

Traditional RAG (Retrieval-Augmented Generation) converts your documents into flat text chunks, turns them into math vectors (embeddings), and searches for chunks that look similar to your query.

**NaviDoc takes a different approach:**
1.  **Structure Extraction**: It reads your document and builds a logical tree of headers and content (e.g., Chapter 1 -> Section 1.1 -> Content).
2.  **Tree Navigation**: When you ask a question, NaviDoc asks the local LLM to look at the top-level headers and choose the most relevant one. It then drills down the tree until it finds the exact content block.
3.  **No Context Blowout**: By only feeding the relevant branch to the LLM, we avoid hitting context limits and prevent the model from getting confused by irrelevant text in other chapters.

---

## 🤝 Contributing & Public Project

NaviDoc is an open-source public project and we welcome contributions from the global community! 

If you want to help make local, private RAG better, please:
1.  **Star** the repository on GitHub.
2.  **Open issues** for bugs or feature requests.
3.  **Submit Pull Requests** to add support for more formats or improve the tree navigation logic.

Let's build the best local RAG tool together!

---

## 📜 License

NaviDoc is open-source software distributed completely free under the **[MIT License](LICENSE)**.
