#\!/bin/bash

# Script to enhance the download progress display

FILE="download-manager.sh"

# 1. Add visual separator before download message (after line 576)
sed -i '576 a\        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"' "$FILE"

# 2. Add file size detection (after "remote_file="${remote_file//\/\//\/}" # Remove double slashes" around line 581-582)
sed -i '/remote_file="${remote_file\/\/\\\/\\\/\\\/}"/ a\        \
        # Get file size for display\
        echo -e "${GRAY}   Fetching file information...${NC}"\
        local file_size=$(ssh -i "${SSH_KEY_PATH}" "${REMOTE_USER}@${REMOTE_HOST}" "stat -f%z '${remote_file}' 2>/dev/null || stat -c%s '${remote_file}' 2>/dev/null")\
        if [[ -n "$file_size" ]] && [[ "$file_size" =~ ^[0-9]+$ ]]; then\
            echo -e "${CYAN}   📊 File Size: ${BOLD}$(format_size $file_size)${NC}"\
        fi\
        \
        echo -e "${YELLOW}   ⏳ Transfer in progress...${NC}"\
        echo ""' "$FILE"

# 3. Update the lftp command to use better progress settings
sed -i 's/get '${remote_file}' -o '${dest_path}\/${file}'/get -O '${dest_path}' '${remote_file}'/' "$FILE"

# 4. Add line after lftp command to capture status
sed -i '/sftp:\/\/${REMOTE_HOST}/ a\        \
        local download_status=$?\
        echo ""' "$FILE"

# 5. Update the success check to use download_status and show file info
sed -i 's/if \[\[ \$? -eq 0 \]\]; then/if [[ $download_status -eq 0 ]]; then/' "$FILE"

# 6. Enhance success message
sed -i 's/print_success "Downloaded: ${file}"/print_success "✓ Downloaded: ${file}"\
            \
            # Show final file location\
            if [[ -f "${dest_path}\/${file}" ]]; then\
                local final_size=$(stat -f%z "${dest_path}\/${file}" 2>\/dev\/null || stat -c%s "${dest_path}\/${file}" 2>\/dev\/null)\
                if [[ -n "$final_size" ]]; then\
                    echo -e "${GREEN}   💾 Saved: $(format_size $final_size) → ${dest_path}\/${file}${NC}"\
                fi\
            fi/' "$FILE"

echo "Enhancement complete\!"
