# xplm-game development helper
# Add this to your ~/.zshrc file
#
# This function automatically uses local code when you're in a repo directory,
# and falls back to the installed version elsewhere.
# It also sets a 5-second timeout for HuggingFace Hub network requests to prevent
# hanging when the network is slow or unavailable.

xplm-game() {
    # Set reasonable timeout for HuggingFace Hub (5 seconds)
    # Only set if not already configured
    if [[ -z "$HF_HUB_ETAG_TIMEOUT" ]]; then
        export HF_HUB_ETAG_TIMEOUT=5
    fi

    # Check if we're in a repo with source code
    if [[ -f "src/xplm_game.py" ]]; then
        # We're in a repo - use local code
        python -m src.xplm_game "$@"
    else
        # Use installed version
        command xplm-game "$@"
    fi
}
