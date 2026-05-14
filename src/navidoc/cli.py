import sys
import os
import subprocess
import platform
import urllib.request

def install_ollama():
    """Download and install Ollama automatically based on OS."""
    system = platform.system()
    print(f"Detected OS: {system}")
    
    if system == "Windows":
        url = "https://ollama.com/download/OllamaSetup.exe"
        installer_path = os.path.join(os.environ.get("TEMP", "."), "OllamaSetup.exe")
        
        print(f"Downloading Ollama installer from {url}...")
        try:
            urllib.request.urlretrieve(url, installer_path)
            print(f"Downloaded to {installer_path}. Running installer...")
            subprocess.run([installer_path], check=True)
            print("Ollama installation process finished.")
        except Exception as e:
            print(f"Failed to install Ollama: {e}")
            print("Please download it manually from https://ollama.com")
            
    elif system == "Linux":
        print("Running Ollama install script (requires curl)...")
        try:
            subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
            print("Ollama installed successfully.")
        except Exception as e:
            print(f"Failed to install Ollama: {e}")
            print("Please install it manually from https://ollama.com")
            
    elif system == "Darwin":
        print("Automatic installation for Mac is not fully supported yet.")
        print("Please download the Mac app from https://ollama.com")
        
    else:
        print(f"Automatic installation not supported for OS: {system}")
        print("Please download Ollama manually from https://ollama.com")

def doctor():
    """Check status of dependencies."""
    print("NaviDoc Doctor - Checking dependencies...\n")
    
    # Check Ollama
    try:
        import ollama
        ollama.list()
        print("[OK] Ollama service is connected.")
    except Exception:
        print("[FAIL] Ollama service is not running or accessible. Run 'navidoc install-ollama' or start it manually.")
        
    # Check Model2Vec
    try:
        from model2vec import StaticModel
        print("[OK] Model2Vec is installed.")
    except ImportError:
        print("[FAIL] Model2Vec is not installed.")
        
    # Check GLM-OCR
    try:
        import glmocr
        print("[OK] GLM-OCR is installed.")
    except ImportError:
        print("[FAIL] GLM-OCR is not installed.")
        
    # Check Sentence Transformers
    try:
        from sentence_transformers import SentenceTransformer
        print("[OK] Sentence-Transformers is installed.")
    except ImportError:
        print("[FAIL] Sentence-Transformers is not installed.")

def main():
    if len(sys.argv) < 2:
        print("NaviDoc CLI - Your local RAG and Ollama helper")
        print("Usage: navidoc <command> [args]")
        print("\nCommands:")
        print("  install-ollama  Download and install Ollama automatically")
        print("  doctor          Check status of dependencies")
        print("  ui              Launch the local Web UI")
        print("  run <model>     Run an Ollama model directly")
        print("  pull <model>    Pull an Ollama model")
        print("  list            List installed Ollama models")
        print("  ollama <args>   Forward any command directly to Ollama")
        return

        
    command = sys.argv[1]
    
    if command == "install-ollama":
        install_ollama()
    elif command == "doctor":
        doctor()
    elif command == "ui":
        try:
            from navidoc.ui import launch_ui
            launch_ui()
        except ImportError:
            print("Error: Gradio is not installed. Please run `pip install gradio`.")
    elif command == "run":

        if len(sys.argv) < 3:
            print("Usage: navidoc run <model>")
            return
        try:
            subprocess.run(["ollama", "run", sys.argv[2]])
        except FileNotFoundError:
            print("Error: Ollama command not found. Is it installed?")
    elif command == "pull":
        if len(sys.argv) < 3:
            print("Usage: navidoc pull <model>")
            return
        try:
            subprocess.run(["ollama", "pull", sys.argv[2]])
        except FileNotFoundError:
            print("Error: Ollama command not found. Is it installed?")
    elif command == "list":
        try:
            subprocess.run(["ollama", "list"])
        except FileNotFoundError:
            print("Error: Ollama command not found. Is it installed?")
    elif command == "ollama":
        try:
            subprocess.run(["ollama"] + sys.argv[2:])
        except FileNotFoundError:
            print("Error: Ollama command not found. Is it installed?")
    else:
        print(f"Unknown command: {command}")
        print("Available commands: install-ollama, doctor, run, pull, list, ollama")

if __name__ == "__main__":
    main()
