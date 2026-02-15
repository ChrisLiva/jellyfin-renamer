#!/bin/bash

# Jellyfin Renamer Install Script
# This script installs the jellyfin-renamer tool to make it available system-wide

set -e

QUIET=false
SKIP_DEPS=false
DRY_RUN=false
INTERACTIVE=true

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

print_status() {
    [[ "$QUIET" == "true" ]] && return
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    [[ "$QUIET" == "true" ]] && return
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

print_header() {
    [[ "$QUIET" == "true" ]] && return
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  Jellyfin Renamer Installer${NC}"
    echo -e "${BLUE}================================${NC}"
}

print_step() {
    [[ "$QUIET" == "true" ]] && return
    echo -e "${CYAN}[STEP]${NC} $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists pacman; then
            echo "arch"
        elif command_exists apt-get; then
            echo "debian"
        elif command_exists dnf; then
            echo "fedora"
        elif command_exists yum; then
            echo "rhel"
        elif command_exists snap; then
            echo "snap"
        else
            echo "linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    else
        echo "unknown"
    fi
}

get_python_version() {
    python3 --version 2>/dev/null | cut -d' ' -f2
}

parse_python_version() {
    local version="$1"
    echo "$version" | cut -d'.' -f1,2
}

check_python_version() {
    local version=$(get_python_version)
    [[ -z "$version" ]] && return 1
    
    local major=$(echo "$version" | cut -d'.' -f1)
    local minor=$(echo "$version" | cut -d'.' -f2)
    
    if [[ $major -lt 3 ]] || ([[ $major -eq 3 ]] && [[ $minor -lt 13 ]]); then
        return 1
    fi
    return 0
}

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-no}"
    
    if [[ "$INTERACTIVE" == "false" ]]; then
        return 0
    fi
    
    if [[ "$default" == "yes" ]]; then
        read -p "$prompt [Y/n]: " -r
    else
        read -p "$prompt [y/N]: " -r
    fi
    echo
    
    if [[ -z "$REPLY" ]]; then
        [[ "$default" == "yes" ]] && return 0 || return 1
    fi
    
    [[ "$REPLY" =~ ^[Yy]$ ]] && return 0 || return 1
}

prompt_timeout() {
    local prompt="$1"
    local timeout="${2:-10}"
    local default="${3:-no}"
    
    if [[ "$INTERACTIVE" == "false" ]]; then
        return 0
    fi
    
    read -t "$timeout" -p "$prompt [y/N]: " -r
    echo
    
    if [[ -z "$REPLY" ]]; then
        [[ "$default" == "yes" ]] && return 0 || return 1
    fi
    
    [[ "$REPLY" =~ ^[Yy]$ ]] && return 0 || return 1
}

install_uv() {
    print_step "Installing UV package manager..."
    
    if command_exists pip3 || command_exists pip; then
        print_status "Installing UV via pip..."
        pip3 install uv 2>/dev/null || pip install uv 2>/dev/null || {
            print_error "Failed to install UV via pip."
            exit 1
        }
        print_status "UV installed successfully!"
        return 0
    fi
    
    if command_exists curl; then
        print_status "Installing UV via official installer..."
        
        if [[ "$QUIET" == "true" ]]; then
            curl -LsSf https://astral.sh/uv/install.sh | sh -s -- -y >/dev/null 2>&1
        else
            curl -LsSf https://astral.sh/uv/install.sh | sh
        fi
        
        if [[ -f "$HOME/.local/bin/uv" ]]; then
            export PATH="$HOME/.local/bin:$PATH"
            print_status "UV installed successfully!"
            return 0
        elif [[ -f "$HOME/.cargo/bin/uv" ]]; then
            export PATH="$HOME/.cargo/bin:$PATH"
            print_status "UV installed successfully!"
            return 0
        else
            print_error "UV installation failed. Please install manually:"
            echo "  pip install uv"
            echo "  or visit: https://docs.astral.sh/uv/getting-started/installation/"
            exit 1
        fi
    else
        print_error "curl or pip is required to install UV."
        print_status "Please install curl or pip first, then run this script again."
        exit 1
    fi
}

install_ffmpeg() {
    local os=$(detect_os)
    
    print_step "Installing FFmpeg..."
    
    if [[ "$os" == "macos" ]]; then
        if command_exists brew; then
            if prompt_yes_no "Install FFmpeg via Homebrew?" "yes"; then
                [[ "$DRY_RUN" == "false" ]] && brew install ffmpeg
                print_status "FFmpeg installed successfully!"
            else
                print_warning "Skipping FFmpeg installation."
            fi
        else
            print_error "Homebrew is required to install FFmpeg on macOS."
            print_status "Please install Homebrew first: https://brew.sh"
            exit 1
        fi
    elif [[ "$os" == "debian" ]] || [[ "$os" == "ubuntu" ]]; then
        if prompt_yes_no "Install FFmpeg via apt-get? (requires sudo)" "yes"; then
            [[ "$DRY_RUN" == "false" ]] && sudo apt-get update && sudo apt-get install -y ffmpeg
            print_status "FFmpeg installed successfully!"
        else
            print_warning "Skipping FFmpeg installation."
        fi
    elif [[ "$os" == "arch" ]]; then
        if prompt_yes_no "Install FFmpeg via pacman? (requires sudo)" "yes"; then
            [[ "$DRY_RUN" == "false" ]] && sudo pacman -Sy --noconfirm ffmpeg
            print_status "FFmpeg installed successfully!"
        else
            print_warning "Skipping FFmpeg installation."
        fi
    elif [[ "$os" == "rhel" ]] || [[ "$os" == "fedora" ]]; then
        if command_exists dnf; then
            if prompt_yes_no "Install FFmpeg via dnf? (requires sudo)" "yes"; then
                [[ "$DRY_RUN" == "false" ]] && sudo dnf install -y ffmpeg
                print_status "FFmpeg installed successfully!"
            else
                print_warning "Skipping FFmpeg installation."
            fi
        elif command_exists yum; then
            if prompt_yes_no "Install FFmpeg via yum? (requires sudo)" "yes"; then
                [[ "$DRY_RUN" == "false" ]] && sudo yum install -y ffmpeg
                print_status "FFmpeg installed successfully!"
            else
                print_warning "Skipping FFmpeg installation."
            fi
        fi
    elif [[ "$os" == "snap" ]]; then
        if prompt_yes_no "Install FFmpeg via snap? (requires sudo)" "yes"; then
            [[ "$DRY_RUN" == "false" ]] && sudo snap install ffmpeg
            print_status "FFmpeg installed successfully!"
        else
            print_warning "Skipping FFmpeg installation."
        fi
    else
        print_warning "Could not install FFmpeg automatically for this OS."
        print_status "Please install FFmpeg manually: https://ffmpeg.org/download.html"
    fi
}

check_already_installed() {
    local script_path="$HOME/.local/bin/jellyfin-renamer"
    if [[ -f "$script_path" ]]; then
        print_warning "jellyfin-renamer appears to already be installed."
        if prompt_yes_no "Reinstall?" "no"; then
            rm -f "$script_path"
            print_status "Removing old installation..."
        else
            print_status "Keeping existing installation. Exiting."
            exit 0
        fi
    fi
}

install_python() {
    print_error "Python 3.13 or higher is required."
    print_status "Current version: $(python3 --version 2>/dev/null || echo 'Python not found')"
    echo
    print_status "Please install Python 3.13+ using one of these methods:"
    echo
    echo -e "  ${CYAN}macOS:${NC}"
    echo "    brew install python@3.13"
    echo
    echo -e "  ${CYAN}Linux (Ubuntu/Debian):${NC}"
    echo "    sudo apt-get install python3.13"
    echo "    # Or use pyenv:"
    echo "    curl https://pyenv.run | bash"
    echo
    echo -e "  ${CYAN}Linux (Arch):${NC}"
    echo "    sudo pacman -S python313"
    echo
    echo -e "  ${CYAN}Windows:${NC}"
    echo "    Download from: https://www.python.org/downloads/"
    echo
    echo -e "  ${CYAN}All platforms (using UV):${NC}"
    echo "    uv python install 3.13"
    echo
    
    if prompt_yes_no "Try to install Python 3.13 using uv?" "yes"; then
        if ! command_exists uv; then
            if [[ "$DRY_RUN" == "true" ]]; then
                print_status "Would install UV package manager."
            else
                print_warning "UV not available. Installing UV first..."
                install_uv
            fi
        fi

        if command_exists uv; then
            if [[ "$DRY_RUN" == "true" ]]; then
                print_status "Would install Python 3.13 with: uv python install 3.13"
            else
                uv python install 3.13
                print_status "Python 3.13 installed! Please restart the installer."
                exit 0
            fi
        else
            print_warning "UV not available. Please install Python manually."
        fi
    fi
    
    exit 1
}

create_executable() {
    local install_dir="$HOME/.local/bin"
    local script_path="$install_dir/jellyfin-renamer"
    local project_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    mkdir -p "$install_dir"
    
    cat > "$script_path" << EOF
#!/bin/bash

SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$project_dir"

if [[ ! -d "\$PROJECT_DIR" ]]; then
    echo "Error: jellyfin-renamer project directory not found at \$PROJECT_DIR"
    echo "Please reinstall the tool."
    exit 1
fi

cd "\$PROJECT_DIR"

if command -v uv >/dev/null 2>&1; then
    uv run python jellyfin-renamer.py "\$@"
else
    python3 jellyfin-renamer.py "\$@"
fi
EOF

    chmod +x "$script_path"
    
    print_status "Created executable at: $script_path"
    
    if [[ ":$PATH:" != *":$install_dir:"* ]]; then
        local profile_file=""
        if [[ -f "$HOME/.bashrc" ]]; then
            profile_file="$HOME/.bashrc"
        elif [[ -f "$HOME/.zshrc" ]]; then
            profile_file="$HOME/.zshrc"
        elif [[ -f "$HOME/.profile" ]]; then
            profile_file="$HOME/.profile"
        fi
        
        if [[ -n "$profile_file" ]]; then
            if ! grep -q "$install_dir" "$profile_file" 2>/dev/null; then
                echo "" >> "$profile_file"
                echo "# Jellyfin Renamer" >> "$profile_file"
                echo "export PATH=\"\$HOME/.local/bin:\$PATH\"" >> "$profile_file"
                print_status "Added PATH export to $profile_file"
            fi
            print_warning "Please restart your terminal or run: source $profile_file"
        else
            print_warning "Could not automatically add to PATH. Add '$install_dir' to your PATH manually."
        fi
    fi
    
    return 0
}

create_desktop_shortcut() {
    if ! command_exists gnome-terminal; then
        print_warning "Skipping desktop shortcut (gnome-terminal not found)."
        return 0
    fi

    if [[ -d "$HOME/Desktop" ]] || [[ -d "$HOME/desktop" ]]; then
        local desktop_dir="$HOME/Desktop"
        [[ -d "$HOME/desktop" ]] && desktop_dir="$HOME/desktop"
        
        local shortcut_path="$desktop_dir/jellyfin-renamer.desktop"
        
        cat > "$shortcut_path" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Jellyfin Renamer
Comment=Organize media files for Jellyfin
Exec=gnome-terminal -- bash -c "jellyfin-renamer --help; exec bash"
Terminal=true
Categories=Utility;
EOF
        chmod +x "$shortcut_path"
        print_status "Created desktop shortcut at: $shortcut_path"
    fi
}

main() {
    for arg in "$@"; do
        case $arg in
            -q|--quiet)
                QUIET=true
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --dry-run)
                DRY_RUN=true
                shift
                ;;
            -y|--yes)
                INTERACTIVE=false
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo
                echo "Options:"
                echo "  -q, --quiet      Quiet mode (minimal output)"
                echo "  --skip-deps      Skip dependency installation"
                echo "  --dry-run        Show what would be done without doing it"
                echo "  -y, --yes        Non-interactive mode (answer yes to prompts)"
                echo "  -h, --help       Show this help message"
                exit 0
                ;;
        esac
    done
    
    print_header
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_warning "Running in DRY-RUN mode - no changes will be made"
        echo
    fi
    
    if [[ ! -f "jellyfin-renamer.py" ]] || [[ ! -f "pyproject.toml" ]]; then
        print_error "Please run this script from the jellyfin-renamer project directory."
        exit 1
    fi
    
    if [[ "$SKIP_DEPS" == "false" ]]; then
        check_already_installed
    fi
    
    print_step "Checking Python version..."
    if ! check_python_version; then
        install_python
    fi
    print_status "Python version OK: $(python3 --version)"
    
    if [[ "$SKIP_DEPS" == "false" ]]; then
        if ! command_exists uv; then
            print_warning "UV package manager not found."
            if prompt_yes_no "Install UV package manager?" "yes"; then
                if [[ "$DRY_RUN" == "true" ]]; then
                    print_status "Would install UV package manager."
                else
                    install_uv
                fi
            fi
        else
            print_status "UV package manager found: $(uv --version)"
        fi

        if [[ "$DRY_RUN" == "false" ]] && ! command_exists uv; then
            print_error "UV is required to install dependencies. Install UV or rerun with --skip-deps."
            exit 1
        fi
        
        if ! command_exists ffmpeg; then
            print_warning "FFmpeg not found."
            if prompt_yes_no "Install FFmpeg?" "yes"; then
                install_ffmpeg
            fi
        else
            print_status "FFmpeg found: $(ffmpeg -version | head -n1)"
        fi
    fi
    
    if [[ "$SKIP_DEPS" == "true" ]]; then
        print_status "Skipping dependency installation (--skip-deps)"
    elif [[ "$DRY_RUN" == "true" ]]; then
        print_status "Would install project dependencies with: uv venv && uv sync"
    else
        print_step "Installing project dependencies..."
        if ! command_exists uv; then
            print_error "UV is required to install dependencies. Install UV or rerun with --skip-deps."
            exit 1
        fi
        uv venv
        uv sync
    fi
    
    print_step "Creating executable..."
    create_executable
    
    if [[ "$DRY_RUN" == "false" ]] && [[ "$INTERACTIVE" == "true" ]]; then
        if prompt_timeout "Create desktop shortcut?" 10 "no"; then
            create_desktop_shortcut
        fi
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        print_status "Would test installation with: jellyfin-renamer --help"
    else
        print_step "Testing installation..."
        if "$HOME/.local/bin/jellyfin-renamer" --help >/dev/null 2>&1; then
            print_status "Installation test successful!"
        else
            print_warning "Installation test failed, but the tool may still work."
        fi
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

main "$@"
