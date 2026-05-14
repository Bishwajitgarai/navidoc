import gradio as gr
from navidoc import NaviDoc
import os

def create_ui():
    # Initialize NaviDoc with default settings
    engine = NaviDoc(use_embeddings=True) # Use embeddings for speed in UI!
    
    with gr.Blocks(title="NaviDoc UI", theme=gr.themes.Soft()) as demo:
        gr.Markdown("""
        # 🗺️ NaviDoc: Premium Local RAG
        Experience the power of Vectorless, Tree-Based RAG directly in your browser. 100% Private.
        """)
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### 📁 Document Ingestion")
                file_input = gr.File(label="Upload New Document", file_types=[".pdf", ".docx", ".md", ".png", ".jpg"])
                ingest_btn = gr.Button("🚀 Ingest Document", variant="primary")
                
                gr.Markdown("---")
                gr.Markdown("### 📚 Available Documents")
                
                # Get available documents from DB and format as (Name, ID)
                docs = engine.db.get_available_documents() if engine.db else []
                choices = [(os.path.basename(doc), doc) for doc in docs]
                
                doc_dropdown = gr.Dropdown(
                    choices=choices, 
                    label="Select a Document", 
                    value=docs[0] if docs else None
                )
                
                with gr.Row():
                    delete_btn = gr.Button("🗑️ Delete Document", variant="stop")
                    refresh_btn = gr.Button("🔄 Refresh List")
                
                status_out = gr.Textbox(label="System Status", interactive=False)
                
                gr.Markdown("""
                ---
                ### ⚙️ Settings
                *   **Model**: phi3
                *   **Navigation**: Model2Vec (32M)
                *   **Storage**: Auto-SQLite
                """)
                
            with gr.Column(scale=3):
                gr.Markdown("### 💬 Chat with Document")
                chatbot = gr.Chatbot(label="Conversation", height=500)
                msg = gr.Textbox(label="Ask a question about the document...", placeholder="Type here and press Enter")
                
                with gr.Row():
                    submit_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("🗑️ Clear Chat History")
                
        def ingest_file(file):
            if file is None:
                return "❌ No file selected.", gr.Dropdown()
            
            print(f"UI Ingesting: {file.name}")
            try:
                res = engine.ingest(file.name)
                # Refresh docs list
                updated_docs = engine.db.get_available_documents() if engine.db else []
                updated_choices = [(os.path.basename(doc), doc) for doc in updated_docs]
                return f"✅ {res}", gr.Dropdown(choices=updated_choices, value=file.name)
            except Exception as e:
                return f"❌ Error: {str(e)}", gr.Dropdown()
            
        def select_doc(doc_id):
            if doc_id:
                engine.current_doc_id = doc_id
                engine.index_type = "sqlite_tree"
                return f"Selected active document: {os.path.basename(doc_id)} (ID: {doc_id})"
            return "No document selected."
            
        def delete_doc(doc_id):
            if not doc_id:
                return "❌ No document selected.", gr.Dropdown()
            print(f"UI Deleting: {doc_id}")
            try:
                engine.db.clear_document(doc_id)
                updated_docs = engine.db.get_available_documents() if engine.db else []
                updated_choices = [(os.path.basename(doc), doc) for doc in updated_docs]
                
                # Reset current doc if deleted
                if engine.current_doc_id == doc_id:
                    engine.current_doc_id = None
                    engine.index_type = None
                    
                new_value = updated_docs[0] if updated_docs else None
                return f"🗑️ Deleted document: {os.path.basename(doc_id)}", gr.Dropdown(choices=updated_choices, value=new_value)
            except Exception as e:
                return f"❌ Error deleting: {str(e)}", gr.Dropdown()
                
        def refresh_list():
            updated_docs = engine.db.get_available_documents() if engine.db else []
            updated_choices = [(os.path.basename(doc), doc) for doc in updated_docs]
            return gr.Dropdown(choices=updated_choices)
            
        def respond(message, chat_history):
            if not engine.index and engine.index_type != "sqlite_tree":
                chat_history.append((message, "⚠️ Please ingest or select a document first!"))
                return "", chat_history
                
            print(f"UI Query on {engine.current_doc_id}: {message}")
            try:
                bot_message = engine.chat(message)
                chat_history.append((message, bot_message))
                return "", chat_history
            except Exception as e:
                chat_history.append((message, f"❌ Error calling backend: {str(e)}"))
                return "", chat_history
            
        def clear_chat():
            engine.clear_history()
            return []
            
        # Event handlers
        ingest_btn.click(ingest_file, inputs=[file_input], outputs=[status_out, doc_dropdown])
        doc_dropdown.change(select_doc, inputs=[doc_dropdown], outputs=[status_out])
        
        delete_btn.click(delete_doc, inputs=[doc_dropdown], outputs=[status_out, doc_dropdown])
        refresh_btn.click(refresh_list, outputs=[doc_dropdown])
        
        msg.submit(respond, inputs=[msg, chatbot], outputs=[msg, chatbot])
        submit_btn.click(respond, inputs=[msg, chatbot], outputs=[msg, chatbot])
        
        clear_btn.click(clear_chat, outputs=[chatbot])
        
    return demo

def launch_ui():
    """Launch the Gradio Web UI."""
    demo = create_ui()
    port = int(os.environ.get("NAVIDOC_PORT", 7860))
    # Share=False as we want it 100% local by default!
    demo.launch(server_name="127.0.0.1", server_port=port, share=False)


if __name__ == "__main__":
    launch_ui()
