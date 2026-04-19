"""
Setup script to initialize the RE Tool environment.
Handles model downloads, database setup, etc.
"""

import os
import sys
import subprocess
from pathlib import Path

# Colors for output
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


def print_header(text):
    """Print a section header."""
    print(f"\n{GREEN}{'='*60}{RESET}")
    print(f"{GREEN}{text.center(60)}{RESET}")
    print(f"{GREEN}{'='*60}{RESET}\n")


def print_success(text):
    """Print success message."""
    print(f"{GREEN}✓{RESET} {text}")


def print_warning(text):
    """Print warning message."""
    print(f"{YELLOW}⚠{RESET} {text}")


def print_error(text):
    """Print error message."""
    print(f"{RED}✗{RESET} {text}")


def check_python_version():
    """Check Python version."""
    print_header("Checking Python Version")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python 3.10+ required, you have {version.major}.{version.minor}")
        return False


def check_cuda():
    """Check CUDA availability."""
    print_header("Checking CUDA/GPU")
    
    try:
        import torch
        if torch.cuda.is_available():
            print_success(f"CUDA Available: {torch.cuda.get_device_name(0)}")
            print_success(f"CUDA Version: {torch.version.cuda}")
            return True
        else:
            print_warning("CUDA not available. CPU mode will be used (slow)")
            return False
    except ImportError:
        print_warning("PyTorch not installed yet")
        return None


def create_directories():
    """Create required directories."""
    print_header("Creating Directories")
    
    dirs = [
        "data/uploads",
        "data/checkpoints",
        "logs",
    ]
    
    for d in dirs:
        path = Path(d)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print_success(f"Created {d}/")
        else:
            print_success(f"Already exists: {d}/")


def create_env_file():
    """Create .env from template if not exists."""
    print_header("Creating .env Configuration")
    
    env_path = Path(".env")
    example_path = Path(".env.example")
    
    if env_path.exists():
        print_success(".env already exists")
        return
    
    if example_path.exists():
        env_path.write_text(example_path.read_text())
        print_success("Created .env from .env.example")
        print_warning("Please edit .env with your configuration")
    else:
        print_error(".env.example not found")


def check_ollama():
    """Check if Ollama is running."""
    print_header("Checking Ollama Service")
    
    try:
        import requests
        response = requests.get("http://localhost:11434/api/version", timeout=5)
        if response.status_code == 200:
            print_success("Ollama is running")
            return True
    except:
        pass
    
    print_warning("Ollama is not running")
    print_warning("Start it with: ollama serve")
    print_warning("Or pull a model: ollama pull llama3")
    return False


def install_dependencies():
    """Install Python dependencies."""
    print_header("Installing Dependencies")
    
    try:
        print("Installing packages from requirements.txt...")
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"],
            check=True
        )
        print_success("Dependencies installed")
        return True
    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        return False


def main():
    """Run setup."""
    print("\n" + "="*60)
    print("Multi-Agentic RE Tool - Backend Setup".center(60))
    print("="*60)
    
    all_ok = True
    
    # 1. Check Python
    if not check_python_version():
        all_ok = False
    
    # 2. Check CUDA
    cuda_status = check_cuda()
    
    # 3. Create directories
    create_directories()
    
    # 4. Create .env
    create_env_file()
    
    # 5. Check Ollama
    if not check_ollama():
        print_warning("Ollama will be needed to run the service")
    
    # 6. Summary
    print_header("Setup Summary")
    
    if all_ok:
        print_success("All checks passed!")
        print("\nNext steps:")
        print("1. Edit .env with your configuration")
        print("2. Start Ollama: ollama serve")
        print("3. Run the backend: python main.py")
    else:
        print_error("Some checks failed. Please resolve and retry.")
    
    # Optional: Install dependencies
    response = input("\nInstall Python dependencies now? (y/n): ").lower()
    if response == 'y':
        if not install_dependencies():
            sys.exit(1)


if __name__ == "__main__":
    main()
