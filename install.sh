#!/bin/bash

# Jellyfin Renamer Install Script
# This script installs the jellyfin-renamer tool to make it available system-wide

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Jellyfin Renamer Installer${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

# Function to get Python version
get_python_version() {
    python3 --version 2>/dev/null | cut -d' ' -f2 | cut -d'.' -f1,2
}

# Function to check Python version
check_python_version() {
    local version=$(get_python_version)
    local major=$(echo $version | cut -d'.' -f1)
    local minor=$(echo $version | cut -d'.' -f2)
    
    if [[ $major -lt 3 ]] || ([[ $major -eq 3 ]] && [[ $minor -lt 13 ]]); then
        return 1
    fi
    return 0
}

# Function to install UV
install_uv() {
    print_status "Installing UV package manager..."
    
    if command_exists curl; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
        export PATH="$HOME/.cargo/bin:$PATH"
        print_status "UV installed successfully!"
    else
        print_error "curl is required to install UV. Please install curl first."
        exit 1
    fi
}

# Function to install FFmpeg
install_ffmpeg() {
    local os=$(detect_os)
    
    print_status "Installing FFmpeg..."
    
    if [[ "$os" == "macos" ]]; then
        if command_exists brew; then
            brew install ffmpeg
        else
            print_error "Homebrew is required to install FFmpeg on macOS."
            print_status "Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif [[ "$os" == "linux" ]]; then
        if command_exists apt-get; then
            sudo apt-get update
            sudo apt-get install -y ffmpeg
        elif command_exists yum; then
            sudo yum install -y ffmpeg
        elif command_exists dnf; then
            sudo dnf install -y ffmpeg
        else
            print_error "Could not install FFmpeg automatically. Please install it manually."
            print_status "Visit: https://ffmpeg.org/download.html"
            exit 1
        fi
    else
        print_error "Could not determine OS for FFmpeg installation."
        print_status "Please install FFmpeg manually: https://ffmpeg.org/download.html"
        exit 1
    fi
    
    print_status "FFmpeg installed successfully!"
}

# Function to create the executable script
create_executable() {
    local install_dir="$HOME/.local/bin"
    local script_path="$install_dir/jellyfin-renamer"
    
    # Create directory if it doesn't exist
    mkdir -p "$install_dir"
    
    # Create the executable script
    cat > "$script_path" << 'EOF'
#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")/jellyfin-renamer"

# Check if the project directory exists
if [[ ! -d "$PROJECT_DIR" ]]; then
    echo "Error: jellyfin-renamer project directory not found at $PROJECT_DIR"
    echo "Please ensure the project is installed correctly."
    exit 1
fi

# Change to the project directory
cd "$PROJECT_DIR"

# Check if UV is available
if command -v uv >/dev/null 2>&1; then
    # Use UV to run the script
    uv run python jellyfin-renamer.py "$@"
else
    # Fallback to direct Python execution
    python3 jellyfin-renamer.py "$@"
fi
EOF

    # Make the script executable
    chmod +x "$script_path"
    
    print_status "Created executable at: $script_path"
    
    # Add to PATH if not already there
    if [[ ":$PATH:" != *":$install_dir:"* ]]; then
        # Add to shell profile
        local profile_file=""
        if [[ -f "$HOME/.bashrc" ]]; then
            profile_file="$HOME/.bashrc"
        elif [[ -f "$HOME/.zshrc" ]]; then
            profile_file="$HOME/.zshrc"
        elif [[ -f "$HOME/.profile" ]]; then
            profile_file="$HOME/.profile"
        fi
        
        if [[ -n "$profile_file" ]]; then
            echo "" >> "$profile_file"
            echo "# Add jellyfin-renamer to PATH" >> "$profile_file"
            echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$profile_file"
            print_status "Added PATH export to $profile_file"
            print_warning "Please restart your terminal or run 'source $profile_file' to use jellyfin-renamer"
        else
            print_warning "Could not automatically add to PATH. Please add '$install_dir' to your PATH manually."
        fi
    fi
    
    return "$script_path"
}

# Function to create desktop shortcut (optional)
create_desktop_shortcut() {
    if [[ -d "$HOME/Desktop" ]]; then
        local desktop_file="$HOME/Desktop/jellyfin-renamer.desktop"
        cat > "$desktop_file" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Jellyfin Renamer
Comment=Organize media files for Jellyfin
Exec=gnome-terminal -- bash -c "jellyfin-renamer --help; exec bash"
Terminal=true
Categories=Utility;
EOF
        chmod +x "$desktop_file"
        print_status "Created desktop shortcut"
    fi
}

# Main installation function
main() {
    print_header
    
    # Check if we're in the right directory
    if [[ ! -f "jellyfin-renamer.py" ]] || [[ ! -f "pyproject.toml" ]]; then
        print_error "Please run this script from the jellyfin-renamer project directory."
        exit 1
    fi
    
    # Check Python version
    print_status "Checking Python version..."
    if ! check_python_version; then
        print_error "Python 3.13 or higher is required."
        print_status "Current version: $(python3 --version 2>/dev/null || echo 'Python not found')"
        exit 1
    fi
    print_status "Python version OK: $(python3 --version)"
    
    # Check/install UV
    if ! command_exists uv; then
        print_warning "UV package manager not found. Installing..."
        install_uv
    else
        print_status "UV package manager found."
    fi
    
    # Check/install FFmpeg
    if ! command_exists ffmpeg; then
        print_warning "FFmpeg not found. Installing..."
        install_ffmpeg
    else
        print_status "FFmpeg found: $(ffmpeg -version | head -n1)"
    fi
    
    # Install project dependencies
    print_status "Installing project dependencies..."
    uv venv
    uv sync
    
    # Create executable
    print_status "Creating executable..."
    local script_path=$(create_executable)
    
    # Create desktop shortcut (optional)
    read -p "Create desktop shortcut? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        create_desktop_shortcut
    fi
    
    # Test the installation
    print_status "Testing installation..."
    if "$script_path" --help >/dev/null 2>&1; then
        print_status "Installation test successful!"
    else
        print_warning "Installation test failed, but the tool may still work."
    fi
    
    echo
    print_status "Installation complete!"
    echo
    echo -e "${GREEN}Usage:${NC}"
    echo "  jellyfin-renamer <source_directory> <target_directory> [options]"
    echo
    echo -e "${GREEN}Examples:${NC}"
    echo "  jellyfin-renamer /path/to/media /path/to/jellyfin/media"
    echo "  jellyfin-renamer /path/to/media /path/to/jellyfin/media --downmix-audio"
    echo "  jellyfin-renamer --help"
    echo
    print_warning "If 'jellyfin-renamer' command is not found, restart your terminal or run:"
    echo "  source ~/.bashrc  # or ~/.zshrc"
    echo
}

# Run main function
main "$@" 