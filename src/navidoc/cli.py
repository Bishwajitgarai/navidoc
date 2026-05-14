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
        # Save to temp directory
        installer_path = os.path.join(os.environ.get("TEMP", "."), "OllamaSetup.exe")
        
        print(f"Downloading Ollama installer from {url}...")
        try:
            urllib.request.urlretrieve(url, installer_path)
            print(f"Downloaded to {installer_path}. Running installer...")
            # Run installer. On Windows, this will usually pop up UAC or the GUI.
            # We don't use silent flags because we want the user to see it and complete it.
            subprocess.run([installer_path], check=True)
            print("Ollama installation process finished.")
        except Exception as e:
            print(f"Failed to install Ollama: {e}")
            print("Please download it manually from https://ollama.com")
            
    elif system == "Linux":
        print("Running Ollama install script (requires curl)...")
        try:
            # This requires curl and sudo permissions usually
            subprocess.run("curl -fsSL https://ollama.com/install.sh | sh", shell=True, check=True)
            print("Ollama installed successfully.")
        except Exception as e:
            print(f"Failed to install Ollama: {e}")
            print("Please install it manually from https://ollama.com")
            
    elif system == "Darwin": # Mac
        print("Automatic installation for Mac is not fully supported yet.")
        print("Please download the Mac app from https://ollama.com")
        
    else:
        print(f"Automatic installation not supported for OS: {system}")
        print("Please download Ollama manually from https://ollama.com")

def main():
    if len(sys.argv) < 2:
        print("NaviDoc CLI")
        print("Usage: navidoc <command>")
        print("Commands:")
        print("  install-ollama  Download and install Ollama automatically")
        return
        
    command = sys.argv[1]
    if command == "install-ollama":
        install_ollama()
    else:
        print(f"Unknown command: {command}")
        print("Available commands: install-ollama")

if __name__ == "__main__":
    main()
