# 🗺️ NaviDoc

NaviDoc is a lightweight, **completely local, zero-API, tree-based RAG (Retrieval-Augmented Generation) framework** designed to navigate document structures intelligently. Instead of blindly chopping your files into arbitrary vector chunks, NaviDoc maps your documents into a logical structural tree hierarchy and uses local LLMs or fast embeddings to precisely steer and navigate to answers.

🔗 **Quick Links:**
*   **PyPI**: [https://pypi.org/project/navidoc/](https://pypi.org/project/navidoc/)
*   **GitHub**: [https://github.com/Bishwajitgarai/navidoc](https://github.com/Bishwajitgarai/navidoc)

---

## 🚀 Key Features

### 🧠 Intelligent Navigation
*   **🌳 Tree-Based RAG**: Mimics human navigation by following document structures (headers, font sizes) instead of standard proximity vector chunks.
*   **🛡️ Dead-End Protection**: The LLM verifies if the navigated section is actually relevant. If not, it falls back to parent content automatically!

### ⚡ Blazing Fast & Hybrid
*   **🚀 Hybrid Navigation**: Optionally use **Model2Vec** (specifically the `potion-base-32M` model) for lightning-fast tree navigation instead of LLM calls! Up to 500x faster and extremely lightweight.
*   **📉 History Limit**: Configurable chat history limits to prevent context blowouts and maintain speed.

### 📄 Enterprise Document Support
*   **Multi-Format Mastery**: Native support for Markdown, PDF (with font-size analysis), DOCX (with style detection), and PPTX.
*   **🖼️ OCR Support**: Ingest images (PNG, JPG) via optional **GLM-OCR** integration!
*   **🗄️ Smart SQLite Storage**: Support for massive PDFs by storing the tree structure in SQLite using a self-referencing hierarchy. **Auto-enables for files > 10MB!**

### 🔒 Privacy & Control
*   **🔒 100% Private & Offline**: Your documents never leave your machine. Zero cloud APIs, zero telemetry.
*   **💬 Persistent Chat**: Maintain conversation history with your documents SDK-style, backed by a localized SQLite database.

---

## ⚙️ How it Works: Vectorless RAG

Traditional RAG converts your documents into flat text chunks, turns them into math vectors (embeddings), and searches for chunks that look similar to your query. 

**NaviDoc takes a better approach:**
1.  **Parse**: It reads your document and builds a tree based on visual structure (e.g., `#` headers in Markdown or large fonts in PDF).
2.  **Navigate**: When you ask a question, it starts at the root and asks the model (LLM or Model2Vec): *"Which of these sections contains the answer?"*
3.  **Refine**: It steps down the tree until it finds the exact leaf node containing the relevant content.
4.  **Answer**: It feeds only that highly specific context to the LLM to generate the final answer.

---

## 🛠️ Getting Started

### 1. Installation

Install NaviDoc via pip or uv:

```bash
pip install navidoc
```


*That's it! All core dependencies like Model2Vec, Sentence-Transformers, and GLM-OCR are now included automatically!*


### 2. Prerequisites

NaviDoc requires **Ollama** to host your local LLM engine.
*   **Auto-Install via NaviDoc CLI**: `navidoc install-ollama`
*   Or download it manually from [ollama.ai](https://ollama.ai/).

### 3. Basic Usage

```python
from navidoc import NaviDoc

# Initialize the engine (Defaults to 'phi3' model)
engine = NaviDoc()

# For super-fast navigation using Model2Vec
# engine = NaviDoc(use_embeddings=True)

# Ingest a document (Auto-detects format)
engine.ingest("user_manual.pdf")

# Query your document offline
response = engine.query("What are the exact system requirements?")
print(response)
```

### 💬 Multi-turn Chat (SDK Style)

NaviDoc remembers conversations!

```python
from navidoc import NaviDoc

engine = NaviDoc(session_id="project_alpha_chat")

engine.ingest("project_plan.docx")

# First turn
print(engine.chat("Who is the project manager?"))

# Second turn (maintains history)
print(engine.chat("What are their primary responsibilities?"))
```

---

## ⌨️ CLI Commands

NaviDoc comes with a powerful CLI to manage your local environment:

*   `navidoc install-ollama`: Auto-downloads and installs Ollama for your OS.
*   `navidoc doctor`: Check status of dependencies.
*   `navidoc run <model>`: Run a specific model.

*   `navidoc pull <model>`: Pull a model.
*   `navidoc list`: List installed models.
*   `navidoc ollama <args>`: Forward any command directly to Ollama.

---

## 🤝 Contributing

We are building the future of local, private document understanding and we want your help! 
Whether you want to add new parsers, optimize the tree navigation, or just improve the docs — all contributions are welcome.

Feel free to open issues or submit PRs on our [GitHub Repository](https://github.com/Bishwajitgarai/navidoc).
