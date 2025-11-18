#!/bin/bash

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 Remote Server Download Manager 📥
# ═══════════════════════════════════════════════════════════════════════════
# A beautiful, user-friendly tool for downloading files from remote servers
# with an emoji-rich, colorful interface designed for ease of use.
# ═══════════════════════════════════════════════════════════════════════════

# ═══════════════════════════════════════════════════════════════════════════
# 🎨 COLOR DEFINITIONS
# ═══════════════════════════════════════════════════════════════════════════

# Text Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
GRAY='\033[0;90m'

# Background Colors
BG_RED='\033[41m'
BG_GREEN='\033[42m'
BG_YELLOW='\033[43m'
BG_BLUE='\033[44m'

# Text Styles
BOLD='\033[1m'
DIM='\033[2m'
UNDERLINE='\033[4m'
BLINK='\033[5m'
REVERSE='\033[7m'

# Reset
NC='\033[0m' # No Color

# ═══════════════════════════════════════════════════════════════════════════
# 📋 GLOBAL VARIABLES
# ═══════════════════════════════════════════════════════════════════════════

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_FILE="${SCRIPT_DIR}/config.conf"
CURRENT_REMOTE_PATH=""
SELECTED_FILES=()
TEMP_DIR="/tmp/dlm_$$"
CACHE_DIR="${SCRIPT_DIR}/.cache"
CACHE_ENABLED=true
CACHE_MAX_AGE=300  # Cache expires after 5 minutes (300 seconds)

# ═══════════════════════════════════════════════════════════════════════════
# 🔧 UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Load configuration file
load_config() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        echo -e "${YELLOW}⚠️  Please create config.conf from the template${NC}"
        exit 1
    fi
    
    source "$CONFIG_FILE"
    
    # Validate required settings
    if [[ -z "$REMOTE_USER" ]] || [[ -z "$REMOTE_HOST" ]]; then
        print_error "Missing required configuration: REMOTE_USER or REMOTE_HOST"
        exit 1
    fi
    
    # Set current path to base path
    CURRENT_REMOTE_PATH="$REMOTE_BASE_PATH"
    
    # Create logs directory if it doesn't exist
    mkdir -p "${SCRIPT_DIR}/logs"
}

# Print functions with colors and emojis
print_header() {
    echo -e "\n${BLUE}${BOLD}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}${BOLD}║  $1${NC}"
    echo -e "${BLUE}${BOLD}╚══════════════════════════════════════════════════════════════╝${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ ERROR: $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_section() {
    echo -e "\n${BLUE}${BOLD}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${BLUE}${BOLD}│  $1${NC}"
    echo -e "${BLUE}${BOLD}└─────────────────────────────────────────────────────────────┘${NC}\n"
}

print_divider() {
    echo -e "${GRAY}─────────────────────────────────────────────────────────────${NC}"
}

# Log function
log_message() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] $1" >> "$LOG_FILE"
}

# Clear screen and show header
show_banner() {
    clear
    echo -e "${CYAN}${BOLD}"
    cat << "EOF"
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║     🚀  REMOTE SERVER DOWNLOAD MANAGER  📥                        ║
║                                                                   ║
║     Making file transfers beautiful and easy!                    ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
}

# Get file emoji based on extension
get_file_emoji() {
    local filename="$1"
    local ext="${filename##*.}"
    ext=$(echo "$ext" | tr '[:upper:]' '[:lower:]') # Convert to lowercase (Bash 3.x compatible)
    
    case "$ext" in
        # Videos
        mp4|mkv|avi|mov|wmv|flv|webm|m4v|mpg|mpeg)
            echo "🎥"
            ;;
        # Audio
        mp3|flac|wav|aac|ogg|m4a|wma|opus)
            echo "🎵"
            ;;
        # Images
        jpg|jpeg|png|gif|bmp|svg|webp|ico|tiff)
            echo "📷"
            ;;
        # Archives
        zip|tar|gz|bz2|7z|rar|xz|tgz)
            echo "📦"
            ;;
        # Documents
        pdf|doc|docx|txt|rtf|odt)
            echo "📝"
            ;;
        # Spreadsheets
        xls|xlsx|csv|ods)
            echo "📊"
            ;;
        # Code
        js|py|sh|bash|java|cpp|c|h|go|rs|php|rb)
            echo "💻"
            ;;
        # Data
        json|xml|yaml|yml|toml|ini|conf)
            echo "💾"
            ;;
        # Executables
        exe|app|dmg|deb|rpm)
            echo "⚙️"
            ;;
        *)
            echo "📄"
            ;;
    esac
}

# Format file size
format_size() {
    local size=$1
    if [[ $size -lt 1024 ]]; then
        echo "${size}B"
    elif [[ $size -lt 1048576 ]]; then
        echo "$(( size / 1024 ))KB"
    elif [[ $size -lt 1073741824 ]]; then
        echo "$(( size / 1048576 ))MB"
    else
        echo "$(( size / 1073741824 ))GB"
    fi
}

# Check if lftp is installed
check_dependencies() {
    if ! command -v lftp &> /dev/null; then
        print_error "lftp is not installed"
        echo -e "${YELLOW}Please install lftp:${NC}"
        echo -e "${CYAN}  • Debian/Ubuntu: sudo apt-get install lftp${NC}"
        echo -e "${CYAN}  • RedHat/CentOS: sudo yum install lftp${NC}"
        echo -e "${CYAN}  • macOS: brew install lftp${NC}"
        exit 1
    fi
}

# Test connection to remote server
test_connection() {
    print_info "Testing connection to ${REMOTE_USER}@${REMOTE_HOST}..."
    
    local test_cmd="lftp -e 'set sftp:connect-program \"ssh -a -x -i ${SSH_KEY_PATH}\"; ls; exit' -u ${REMOTE_USER}, sftp://${REMOTE_HOST}"
        
        local download_status=$?
        echo ""
    
    if eval "$test_cmd" &> /dev/null; then
        print_success "Connection successful!"
        return 0
    else
        print_error "Connection failed!"
        print_warning "Please check your configuration and SSH key"
        return 1
    fi
}

# ═══════════════════════════════════════════════════════════════════════════
# 📁 REMOTE FILE OPERATIONS
# ═══════════════════════════════════════════════════════════════════════════

# List remote directory contents with detailed information
list_remote_directory() {
    local path="$1"
    local force_refresh="${2:-false}"

    # Create temp and cache directories
    mkdir -p "$TEMP_DIR"
    mkdir -p "$CACHE_DIR"

    # Generate cache filename from path (replace / with _)
    local cache_key=$(echo "$path" | sed 's/\//_/g')
    local cache_file="${CACHE_DIR}/listing_${cache_key}.cache"
    local cache_time_file="${cache_file}.time"

    # Check if we should use cache
    local use_cache=false
    if [[ "$CACHE_ENABLED" == "true" ]] && [[ "$force_refresh" != "true" ]] && [[ -f "$cache_file" ]] && [[ -f "$cache_time_file" ]]; then
        local cache_timestamp=$(cat "$cache_time_file")
        local current_time=$(date +%s)
        local cache_age=$((current_time - cache_timestamp))

        if [[ $cache_age -lt $CACHE_MAX_AGE ]]; then
            use_cache=true
            # Copy cache to temp location
            cp "$cache_file" "${TEMP_DIR}/listing.txt"

            # Show cache age
            local minutes=$((cache_age / 60))
            local seconds=$((cache_age % 60))
            if [[ $minutes -gt 0 ]]; then
                echo -e "${DIM}   📦 Using cached data (${minutes}m ${seconds}s old)${NC}"
            else
                echo -e "${DIM}   📦 Using cached data (${seconds}s old)${NC}"
            fi
        fi
    fi

    # Fetch from remote if cache not used
    if [[ "$use_cache" != "true" ]]; then
        echo -e "${DIM}   🔄 Fetching directory listing...${NC}"

        # Get detailed directory listing with modification time
        lftp -e "set sftp:connect-program \"ssh -a -x -i ${SSH_KEY_PATH}\"; cd '$path'; cls -l --sort=date; exit" -u "${REMOTE_USER}," sftp://${REMOTE_HOST} 2>/dev/null > "${TEMP_DIR}/listing.txt"

        if [[ $? -ne 0 ]]; then
            print_error "Failed to list directory: $path"
            return 1
        fi

        # Save to cache
        if [[ "$CACHE_ENABLED" == "true" ]]; then
            cp "${TEMP_DIR}/listing.txt" "$cache_file"
            date +%s > "$cache_time_file"
        fi
    fi

    return 0
}

# Get file details (size, type)
get_file_details() {
    local path="$1"
    local filename="$2"
    
    # Get file info using lftp
    local info=$(lftp -e "set sftp:connect-program \"ssh -a -x -i ${SSH_KEY_PATH}\"; cd '$path'; cls -l '$filename'; exit" -u "${REMOTE_USER}," sftp://${REMOTE_HOST} 2>/dev/null)
        
        local download_status=$?
        echo ""
    
    # Parse size from ls -l output
    local size=$(echo "$info" | awk '{print $5}')
    
    echo "$size"
}

# Check if path is a directory
is_directory() {
    local path="$1"
    local name="$2"
    
    # Try to list the path - if it succeeds, it's a directory
    lftp -e "set sftp:connect-program \"ssh -a -x -i ${SSH_KEY_PATH}\"; cd '$path/$name'; exit" -u "${REMOTE_USER}," sftp://${REMOTE_HOST} &>/dev/null
        
        local download_status=$?
        echo ""
    return $?
}

# ═══════════════════════════════════════════════════════════════════════════
# 🎯 INTERACTIVE MENU FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Display file browser
show_file_browser() {
    while true; do
        show_banner
        
        # Show connection status
        echo -e "${GREEN}🔗 Connected to: ${BOLD}${REMOTE_USER}@${REMOTE_HOST}${NC}"
        echo -e "${CYAN}📁 Current Path: ${BOLD}${CURRENT_REMOTE_PATH}${NC}\n"
        
        print_divider
        
        # List directory contents
        if ! list_remote_directory "$CURRENT_REMOTE_PATH"; then
            print_error "Failed to access directory"
            read -p "Press Enter to return to main menu..."
            return
        fi
        
        # Read and display files
        local -a items=()
        local -a types=()
        local index=1
        
        # Add navigation options
        if [[ "$CURRENT_REMOTE_PATH" != "$REMOTE_BASE_PATH" ]]; then
            echo -e "${YELLOW}  0. 🏠 Back to base directory${NC}"
            echo -e "${YELLOW}  .. ⬆️  Go up one level${NC}"
            print_divider
        fi
        
        # Read files from detailed listing (ls -l format sorted by date)
        while IFS= read -r line; do
            [[ -z "$line" ]] && continue
            
            # Parse ls -l output format:
            # drwxr-xr-x  5 user group  4096 Nov 14 10:30 folder_name
            # -rw-r--r--  1 user group  1234 Nov 14 10:25 file.txt
            
            # Extract file type (first character: d=directory, -=file, l=link)
            local file_type="${line:0:1}"
            
            # Extract date and time (columns 6, 7, 8)
            local date_info=$(echo "$line" | awk '{print $6, $7, $8}')
            
            # Extract filename (everything after the date/time, which is columns 6-8)
            # Use awk to get the filename (field 9 onwards)
            local filename=$(echo "$line" | awk '{for(i=9;i<=NF;i++) printf "%s%s", $i, (i<NF?" ":""); print ""}')
            
            # Skip if filename is empty or is . or ..
            [[ -z "$filename" || "$filename" == "." || "$filename" == ".." ]] && continue
            
            # Truncate long filenames for better display (max 50 chars)
            local display_name="$filename"
            if [[ ${#filename} -gt 50 ]]; then
                display_name="${filename:0:47}..."
            fi
            
            # Check if it's a directory
            if [[ "$file_type" == "d" ]]; then
                # Format: index + emoji + name (left-aligned, 55 chars) + date (right-aligned)
                printf "${CYAN}  %3d. 📁 ${BOLD}%-55s${NC} ${DIM}[%s]${NC}\n" "$index" "${display_name}/" "$date_info"
                items+=("$filename")
                types+=("dir")
            else
                local emoji=$(get_file_emoji "$filename")
                local size_display=""
                
                # Extract file size (column 5) if enabled
                if [[ "$SHOW_FILE_SIZES" == "true" ]]; then
                    local file_size=$(echo "$line" | awk '{print $5}')
                    if [[ -n "$file_size" ]] && [[ "$file_size" =~ ^[0-9]+$ ]] && [[ "$file_size" != "0" ]]; then
                        size_display="$(format_size $file_size)"
                    fi
                fi
                
                # Format: index + emoji + name (left-aligned, 45 chars) + size (right-aligned, 8 chars) + date
                if [[ -n "$size_display" ]]; then
                    printf "${WHITE}  %3d. %s %-45s${NC} ${GRAY}%8s${NC} ${DIM}[%s]${NC}\n" "$index" "$emoji" "$display_name" "($size_display)" "$date_info"
                else
                    printf "${WHITE}  %3d. %s %-45s${NC}          ${DIM}[%s]${NC}\n" "$index" "$emoji" "$display_name" "$date_info"
                fi
                
                items+=("$filename")
                types+=("file")
            fi
            
            ((index++))
        done < "${TEMP_DIR}/listing.txt"
        
        print_divider
        
        # Show options
        echo -e "\n${BLUE}${BOLD}Options:${NC}"
        echo -e "${WHITE}  • Enter number to select${NC}"
        echo -e "${WHITE}  • Multiple files: ${CYAN}1,3,5${WHITE} or ${CYAN}2-6${NC}"
        echo -e "${WHITE}  • Type ${CYAN}'all'${WHITE} to select all files${NC}"
        echo -e "${WHITE}  • Type ${CYAN}'r'${WHITE} to refresh directory listing${NC}"
        echo -e "${WHITE}  • Type ${CYAN}'q'${WHITE} to return to main menu${NC}"

        if [[ "$CURRENT_REMOTE_PATH" != "$REMOTE_BASE_PATH" ]]; then
            echo -e "${WHITE}  • Type ${CYAN}'..'${WHITE} to go up${NC}"
        fi
        
        echo -e -n "\n${MAGENTA}${BOLD}➤ Your choice: ${NC}"
        read -r choice
        
        # Handle input
        case "$choice" in
            q|Q)
                return
                ;;
            ..)
                if [[ "$CURRENT_REMOTE_PATH" != "$REMOTE_BASE_PATH" ]]; then
                    CURRENT_REMOTE_PATH=$(dirname "$CURRENT_REMOTE_PATH")
                fi
                ;;
            0)
                CURRENT_REMOTE_PATH="$REMOTE_BASE_PATH"
                ;;
            all|ALL)
                # Select all files (not directories)
                SELECTED_FILES=()
                for i in "${!types[@]}"; do
                    if [[ "${types[$i]}" == "file" ]]; then
                        SELECTED_FILES+=("${items[$i]}")
                    fi
                done

                if [[ ${#SELECTED_FILES[@]} -gt 0 ]]; then
                    show_download_menu
                else
                    print_warning "No files to select"
                    read -p "Press Enter to continue..."
                fi
                ;;
            r|R)
                # Force refresh directory listing
                echo -e "${CYAN}🔄 Refreshing directory listing...${NC}"
                list_remote_directory "$CURRENT_REMOTE_PATH" "true"
                sleep 1
                ;;
            *[0-9]*)
                handle_selection "$choice" items types
                ;;
            *)
                print_warning "Invalid choice"
                sleep 1
                ;;
        esac
    done
}

# Handle file/directory selection
handle_selection() {
    local input="$1"
    local -n items_ref=$2
    local -n types_ref=$3
    
    # Parse selection (handle ranges and comma-separated)
    local -a selected_indices=()
    
    # Handle comma-separated values
    IFS=',' read -ra PARTS <<< "$input"
    for part in "${PARTS[@]}"; do
        part=$(echo "$part" | xargs) # Trim whitespace
        
        # Handle ranges (e.g., 2-5)
        if [[ "$part" =~ ^([0-9]+)-([0-9]+)$ ]]; then
            local start="${BASH_REMATCH[1]}"
            local end="${BASH_REMATCH[2]}"
            for ((i=start; i<=end; i++)); do
                selected_indices+=($i)
            done
        # Handle single numbers
        elif [[ "$part" =~ ^[0-9]+$ ]]; then
            selected_indices+=($part)
        fi
    done
    
    # Process selections
    SELECTED_FILES=()
    local has_directory=false
    
    for idx in "${selected_indices[@]}"; do
        local array_idx=$((idx - 1))
        
        if [[ $array_idx -ge 0 ]] && [[ $array_idx -lt ${#items_ref[@]} ]]; then
            local item="${items_ref[$array_idx]}"
            local item_type="${types_ref[$array_idx]}"
            
            # Check if it's a directory using pre-parsed type
            if [[ "$item_type" == "dir" ]]; then
                # Navigate into directory
                CURRENT_REMOTE_PATH="${CURRENT_REMOTE_PATH}/${item}"
                CURRENT_REMOTE_PATH="${CURRENT_REMOTE_PATH//\/\//\/}" # Remove double slashes
                has_directory=true
                break
            else
                SELECTED_FILES+=("$item")
            fi
        fi
    done
    
    # If we navigated into a directory, return to show new listing
    if [[ "$has_directory" == "true" ]]; then
        return
    fi
    
    # If files were selected, show download menu
    if [[ ${#SELECTED_FILES[@]} -gt 0 ]]; then
        show_download_menu
    fi
}

# Show download destination menu
show_download_menu() {
    show_banner
    
    print_section "📥 Selected Files for Download"
    
    for file in "${SELECTED_FILES[@]}"; do
        local emoji=$(get_file_emoji "$file")
        echo -e "${WHITE}  ${emoji} ${file}${NC}"
    done
    
    print_divider
    
    print_section "📍 Choose Download Destination"
    
    local -a paths=()
    local -a names=()
    local index=1
    
    # Build list of configured paths
    for i in {1..5}; do
        local path_var="DOWNLOAD_PATH_${i}"
        local name_var="PATH_${i}_NAME"
        
        if [[ -n "${!path_var}" ]]; then
            paths+=("${!path_var}")
            names+=("${!name_var}")
            echo -e "${CYAN}  ${index}. ${!name_var} ${GRAY}(${!path_var})${NC}"
            ((index++))
        fi
    done
    
    echo -e "${CYAN}  ${index}. 📝 Custom path${NC}"
    echo -e "${YELLOW}  0. ❌ Cancel${NC}"
    
    echo -e -n "\n${MAGENTA}${BOLD}➤ Select destination: ${NC}"
    read -r dest_choice
    
    if [[ "$dest_choice" == "0" ]]; then
        SELECTED_FILES=()
        return
    elif [[ "$dest_choice" == "$index" ]]; then
        echo -e -n "${CYAN}Enter custom path: ${NC}"
        read -r custom_path
        
        if [[ -z "$custom_path" ]]; then
            print_warning "No path entered"
            read -p "Press Enter to continue..."
            return
        fi
        
        download_files "$custom_path"
    elif [[ "$dest_choice" =~ ^[0-9]+$ ]] && [[ $dest_choice -ge 1 ]] && [[ $dest_choice -lt $index ]]; then
        local path_idx=$((dest_choice - 1))
        download_files "${paths[$path_idx]}"
    else
        print_warning "Invalid choice"
        read -p "Press Enter to continue..."
    fi
}

# Download selected files
download_files() {
    local dest_path="$1"
    
    # Create destination directory if it doesn't exist
    if [[ ! -d "$dest_path" ]]; then
        print_warning "Destination directory doesn't exist: $dest_path"
        echo -e -n "${YELLOW}Create it? (y/n): ${NC}"
        read -r create_dir
        
        if [[ "$create_dir" =~ ^[Yy]$ ]]; then
            mkdir -p "$dest_path"
            if [[ $? -ne 0 ]]; then
                print_error "Failed to create directory"
                read -p "Press Enter to continue..."
                return
            fi
        else
            return
        fi
    fi
    
    show_banner
    print_section "📥 Downloading Files"
    
    echo -e "${CYAN}Source: ${BOLD}${CURRENT_REMOTE_PATH}${NC}"
    echo -e "${CYAN}Destination: ${BOLD}${dest_path}${NC}\n"
    
    print_divider
    
    local success_count=0
    local fail_count=0
    
    for file in "${SELECTED_FILES[@]}"; do
        local emoji=$(get_file_emoji "$file")
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "\n${BLUE}📥 Downloading: ${emoji} ${BOLD}${file}${NC}"
        
        # Build lftp command
        local remote_file="${CURRENT_REMOTE_PATH}/${file}"
        remote_file="${remote_file//\/\//\/}" # Remove double slashes

        # Get file size for display
        echo -e "${GRAY}   Fetching file information...${NC}"
        # Properly escape the remote file path for SSH
        local escaped_remote_file=$(printf '%q' "$remote_file")
        local file_size=$(ssh -i "${SSH_KEY_PATH}" "${REMOTE_USER}@${REMOTE_HOST}" "stat -c%s ${escaped_remote_file} 2>/dev/null || stat -f%z ${escaped_remote_file} 2>/dev/null")
        if [[ -n "$file_size" ]] && [[ "$file_size" =~ ^[0-9]+$ ]]; then
            echo -e "${CYAN}   📊 File Size: ${BOLD}$(format_size $file_size)${NC}"
        fi

        echo -e "${YELLOW}   ⏳ Transfer in progress...${NC}"
        echo ""

        # Download with progress - use temp script to avoid escaping issues with special characters
        local lftp_script="${TEMP_DIR}/lftp_script_$$.txt"
        # Write lftp script with proper quoting and performance optimizations
        {
            # SSH optimization: use faster cipher and disable compression
            echo "set sftp:connect-program \"ssh -a -x -o Compression=no -o Ciphers=aes128-gcm@openssh.com,aes128-ctr -i ${SSH_KEY_PATH}\""

            # Transfer settings
            echo "set xfer:clobber on"

            # Network settings
            echo "set net:timeout 30"
            echo "set net:reconnect-interval-base 5"
            echo "set net:max-retries 3"
            echo "set net:connection-limit 4"
            echo "set net:socket-buffer 524288"

            # SFTP specific optimizations
            echo "set sftp:max-packets-in-flight 64"
            echo "set sftp:size-read 262144"
            echo "set sftp:size-write 262144"

            # Buffer size for transfers
            echo "set xfer:buffer-size 524288"

            printf 'cd "%s"\n' "$(dirname "$remote_file")"
            printf 'get -O "%s" "%s"\n' "$dest_path" "$(basename "$remote_file")"
            echo "exit"
        } > "$lftp_script"

        # Execute lftp with the script file
        lftp -u "${REMOTE_USER}," sftp://${REMOTE_HOST} < "$lftp_script"
        local download_status=$?
        rm -f "$lftp_script"
        echo ""

        if [[ $download_status -eq 0 ]]; then
            print_success "✓ Downloaded: ${file}"
            
            # Show final file location
            if [[ -f "${dest_path}/${file}" ]]; then
                local final_size=$(stat -f%z "${dest_path}/${file}" 2>/dev/null || stat -c%s "${dest_path}/${file}" 2>/dev/null)
                if [[ -n "$final_size" ]]; then
                    echo -e "${GREEN}   💾 Saved: $(format_size $final_size) → ${dest_path}/${file}${NC}"
                fi
            fi
            log_message "SUCCESS: Downloaded ${remote_file} to ${dest_path}/${file}"
            ((success_count++))
        else
            print_error "Failed: ${file}"
            log_message "FAILED: Download of ${remote_file} to ${dest_path}/${file}"
            ((fail_count++))
        fi
    done
    
    print_divider
    
    # Show summary
    echo -e "\n${BOLD}📊 Download Summary:${NC}"
    echo -e "${GREEN}  ✅ Successful: ${success_count}${NC}"
    
    if [[ $fail_count -gt 0 ]]; then
        echo -e "${RED}  ❌ Failed: ${fail_count}${NC}"
    fi
    
    echo -e "\n${CYAN}Files saved to: ${BOLD}${dest_path}${NC}"
    
    # Clear selected files
    SELECTED_FILES=()
    
    read -p $'\n'"Press Enter to continue..."
}

# ═══════════════════════════════════════════════════════════════════════════
# 🎮 MAIN MENU
# ═══════════════════════════════════════════════════════════════════════════

# Clear cache
clear_cache() {
    show_banner
    print_section "🗑️  Cache Management"

    if [[ ! -d "$CACHE_DIR" ]] || [[ -z "$(ls -A "$CACHE_DIR" 2>/dev/null)" ]]; then
        print_info "Cache is already empty"
        read -p $'\n'"Press Enter to continue..."
        return
    fi

    # Show cache stats
    local cache_count=$(find "$CACHE_DIR" -name "*.cache" 2>/dev/null | wc -l | xargs)
    local cache_size=$(du -sh "$CACHE_DIR" 2>/dev/null | awk '{print $1}')

    echo -e "${CYAN}Current cache:${NC}"
    echo -e "${WHITE}  • Cached directories: ${BOLD}${cache_count}${NC}"
    echo -e "${WHITE}  • Cache size: ${BOLD}${cache_size}${NC}\n"

    echo -e -n "${YELLOW}Are you sure you want to clear the cache? (y/n): ${NC}"
    read -r confirm

    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        rm -rf "${CACHE_DIR}"/*
        print_success "Cache cleared successfully"
    else
        print_info "Cache clear cancelled"
    fi

    read -p $'\n'"Press Enter to continue..."
}

show_main_menu() {
    while true; do
        show_banner
        
        echo -e "${GREEN}🔗 Server: ${BOLD}${REMOTE_USER}@${REMOTE_HOST}${NC}"
        echo -e "${CYAN}📁 Base Path: ${BOLD}${REMOTE_BASE_PATH}${NC}\n"
        
        print_divider
        
        print_section "🎯 Main Menu"
        
        echo -e "${CYAN}  1. 📁 Browse Remote Server${NC}"
        echo -e "${CYAN}  2. ⚙️  Configure Settings${NC}"
        echo -e "${CYAN}  3. 📝 View Download Logs${NC}"
        echo -e "${CYAN}  4. 🔍 Test Connection${NC}"
        echo -e "${CYAN}  5. 🗑️  Clear Cache${NC}"
        echo -e "${CYAN}  6. ❓ Help${NC}"
        echo -e "${RED}  0. 🚪 Exit${NC}"
        
        print_divider
        
        echo -e -n "\n${MAGENTA}${BOLD}➤ Select option: ${NC}"
        read -r choice
        
        case "$choice" in
            1)
                show_file_browser
                ;;
            2)
                show_config_menu
                ;;
            3)
                show_logs
                ;;
            4)
                test_connection
                read -p "Press Enter to continue..."
                ;;
            5)
                clear_cache
                ;;
            6)
                show_help
                ;;
            0)
                echo -e "\n${GREEN}👋 Thanks for using Remote Server Download Manager!${NC}\n"
                cleanup
                exit 0
                ;;
            *)
                print_warning "Invalid option"
                sleep 1
                ;;
        esac
    done
}

# Show configuration menu
show_config_menu() {
    show_banner
    print_section "⚙️  Configuration"
    
    echo -e "${CYAN}Configuration file: ${BOLD}${CONFIG_FILE}${NC}\n"
    
    echo -e "${WHITE}Current Settings:${NC}"
    echo -e "${CYAN}  • Remote User: ${BOLD}${REMOTE_USER}${NC}"
    echo -e "${CYAN}  • Remote Host: ${BOLD}${REMOTE_HOST}${NC}"
    echo -e "${CYAN}  • Base Path: ${BOLD}${REMOTE_BASE_PATH}${NC}"
    echo -e "${CYAN}  • SSH Key: ${BOLD}${SSH_KEY_PATH}${NC}"
    
    print_divider
    
    echo -e "\n${YELLOW}To modify settings, edit the configuration file:${NC}"
    echo -e "${CYAN}  nano ${CONFIG_FILE}${NC}"
    
    read -p $'\n'"Press Enter to continue..."
}

# Show logs
show_logs() {
    show_banner
    print_section "📝 Recent Download Logs"
    
    if [[ -f "$LOG_FILE" ]]; then
        tail -n 20 "$LOG_FILE"
    else
        print_info "No logs found"
    fi
    
    read -p $'\n'"Press Enter to continue..."
}

# Show help
show_help() {
    show_banner
    print_section "❓ Help & Tips"
    
    cat << EOF
${CYAN}${BOLD}Navigation:${NC}
  • Use numbers to select files or folders
  • Enter folders by selecting their number
  • Use '..' to go up one directory level
  • Use '0' to return to base directory

${CYAN}${BOLD}File Selection:${NC}
  • Single file: ${WHITE}3${NC}
  • Multiple files: ${WHITE}1,3,5${NC}
  • Range: ${WHITE}2-6${NC}
  • All files: ${WHITE}all${NC}

${CYAN}${BOLD}Emoji Guide:${NC}
  📁 Folders          🎥 Videos          🎵 Audio
  📷 Images           📦 Archives        📝 Documents
  💾 Data files       💻 Code files      📄 Other files

${CYAN}${BOLD}Color Guide:${NC}
  ${GREEN}Green${NC} - Success messages
  ${BLUE}Blue${NC} - Headers and menus
  ${YELLOW}Yellow${NC} - Warnings
  ${RED}Red${NC} - Errors
  ${CYAN}Cyan${NC} - Information

${CYAN}${BOLD}Tips:${NC}
  • Configure your settings in config.conf
  • Check logs if downloads fail
  • Test connection before browsing
  • Use pre-configured paths for quick downloads

${CYAN}${BOLD}Troubleshooting:${NC}
  • Ensure lftp is installed
  • Verify SSH key permissions (chmod 600)
  • Test SSH connection manually
  • Check paths in config.conf

EOF
    
    read -p "Press Enter to continue..."
}

# Cleanup function
cleanup() {
    rm -rf "$TEMP_DIR"
}

# ═══════════════════════════════════════════════════════════════════════════
# 🗄️  DATABASE MODE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

# Download files from database queue
download_from_database() {
    local scanner_script="${SCRIPT_DIR}/remote_scanner.py"

    # Check if Python script exists
    if [[ ! -f "$scanner_script" ]]; then
        print_error "Remote scanner script not found: $scanner_script"
        exit 1
    fi

    # Get queued files from database
    print_info "Loading queued files from database..."
    local queue_json=$(python3 "$scanner_script" --export-queue)

    # Check if queue is empty
    if [[ "$queue_json" == "[]" ]]; then
        print_warning "No files queued for download"
        echo -e "${YELLOW}Use: python3 remote_scanner.py --queue <IDs>${NC}"
        exit 0
    fi

    # Parse JSON and download files
    local file_count=$(echo "$queue_json" | python3 -c "import sys, json; print(len(json.load(sys.stdin)))")

    show_banner
    print_section "📥 Database-Driven Download Mode"

    echo -e "${CYAN}Found ${BOLD}${file_count}${NC}${CYAN} file(s) queued for download${NC}\n"

    show_banner
    print_section "📥 Downloading Queued Files"

    print_info "Files will be downloaded to their specified destinations"
    print_divider

    local success_count=0
    local fail_count=0

    # Process each file in the queue
    echo "$queue_json" | python3 -c "
import sys, json
for item in json.load(sys.stdin):
    local_path = item.get('local_path', '') or ''
    print(f\"{item['download_id']}|{item['file_id']}|{item['remote_path']}|{item['filename']}|{local_path}\")
" | while IFS='|' read -r download_id file_id remote_path filename local_path; do

        local emoji=$(get_file_emoji "$filename")

        # Determine destination path
        if [[ -n "$local_path" ]]; then
            local dest_path="$local_path"
        else
            # Use default path if no specific destination
            local dest_path="${DOWNLOAD_PATH_1}"
        fi

        # Create destination directory if it doesn't exist
        if [[ ! -d "$dest_path" ]]; then
            mkdir -p "$dest_path"
        fi

        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "\n${BLUE}📥 Downloading: ${emoji} ${BOLD}${filename}${NC}"
        echo -e "${GRAY}   Destination: ${dest_path}${NC}"

        # Build lftp command
        local remote_file="${remote_path}/${filename}"
        remote_file="${remote_file//\/\//\/}" # Remove double slashes

        # Get file size for display
        echo -e "${GRAY}   Fetching file information...${NC}"
        # Properly escape the remote file path for SSH
        local escaped_remote_file=$(printf '%q' "$remote_file")
        local file_size=$(ssh -i "${SSH_KEY_PATH}" "${REMOTE_USER}@${REMOTE_HOST}" "stat -c%s ${escaped_remote_file} 2>/dev/null || stat -f%z ${escaped_remote_file} 2>/dev/null")
        if [[ -n "$file_size" ]] && [[ "$file_size" =~ ^[0-9]+$ ]]; then
            echo -e "${CYAN}   📊 File Size: ${BOLD}$(format_size $file_size)${NC}"
        fi

        echo -e "${YELLOW}   ⏳ Transfer in progress...${NC}"
        echo ""

        # Download with progress - use temp script to avoid escaping issues with special characters
        local lftp_script="${TEMP_DIR}/lftp_script_db_$$.txt"
        # Write lftp script with proper quoting and performance optimizations
        {
            # SSH optimization: use faster cipher and disable compression
            echo "set sftp:connect-program \"ssh -a -x -o Compression=no -o Ciphers=aes128-gcm@openssh.com,aes128-ctr -i ${SSH_KEY_PATH}\""

            # Transfer settings
            echo "set xfer:clobber on"

            # Network settings
            echo "set net:timeout 30"
            echo "set net:reconnect-interval-base 5"
            echo "set net:max-retries 3"
            echo "set net:connection-limit 4"
            echo "set net:socket-buffer 524288"

            # SFTP specific optimizations
            echo "set sftp:max-packets-in-flight 64"
            echo "set sftp:size-read 262144"
            echo "set sftp:size-write 262144"

            # Buffer size for transfers
            echo "set xfer:buffer-size 524288"

            printf 'cd "%s"\n' "$(dirname "$remote_file")"
            printf 'get -O "%s" "%s"\n' "$dest_path" "$(basename "$remote_file")"
            echo "exit"
        } > "$lftp_script"

        # Execute lftp with the script file
        lftp -u "${REMOTE_USER}," sftp://${REMOTE_HOST} < "$lftp_script"
        local download_status=$?
        rm -f "$lftp_script"
        echo ""

        if [[ $download_status -eq 0 ]]; then
            print_success "✓ Downloaded: ${filename}"

            # Show final file location
            if [[ -f "${dest_path}/${filename}" ]]; then
                local final_size=$(stat -f%z "${dest_path}/${filename}" 2>/dev/null || stat -c%s "${dest_path}/${filename}" 2>/dev/null)
                if [[ -n "$final_size" ]]; then
                    echo -e "${GREEN}   💾 Saved: $(format_size $final_size) → ${dest_path}/${filename}${NC}"
                fi
            fi

            log_message "SUCCESS: Downloaded ${remote_file} to ${dest_path}/${filename}"

            # Mark as completed in database
            python3 "$scanner_script" --mark-complete "$download_id" "${dest_path}/${filename}" &>/dev/null

            ((success_count++))
        else
            print_error "Failed: ${filename}"
            log_message "FAILED: Download of ${remote_file} to ${dest_path}/${filename}"

            # Mark as failed in database
            python3 "$scanner_script" --mark-failed "$download_id" &>/dev/null

            ((fail_count++))
        fi
    done

    print_divider

    # Show summary
    echo -e "\n${BOLD}📊 Download Summary:${NC}"
    echo -e "${GREEN}  ✅ Successful: ${success_count}${NC}"

    if [[ $fail_count -gt 0 ]]; then
        echo -e "${RED}  ❌ Failed: ${fail_count}${NC}"
    fi

    echo -e "\n${CYAN}Files saved to: ${BOLD}${dest_path}${NC}"
    print_info "Download records updated in database"
}

# ═══════════════════════════════════════════════════════════════════════════
# 🚀 MAIN EXECUTION
# ═══════════════════════════════════════════════════════════════════════════

main() {
    # Set up cleanup trap
    trap cleanup EXIT

    # Check dependencies
    check_dependencies

    # Load configuration
    load_config

    # Check for database mode flag
    if [[ "$1" == "--from-db" ]]; then
        download_from_database
        exit 0
    fi

    # Show main menu
    show_main_menu
}

# Run main function
main "$@"