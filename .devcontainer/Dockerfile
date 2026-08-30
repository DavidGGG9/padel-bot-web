# Use a specific digest or version for reproducibility
FROM python:3.13-slim

# 1. Grab uv from the official image (Much faster & cleaner than curl)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set environment variables
ENV USER=david \
    HOME=/app \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # Place uv binaries and the venv in the PATH
    PATH="/app/.local/bin:/app/.venv/bin:$PATH"

WORKDIR $HOME

# 2. Combine system dependencies to reduce layers
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    make \
    zsh \
    htop \
    openssh-client \
    gettext-base \
    zip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y --no-install-recommends nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 3. Create the user FIRST
RUN useradd -m -s /bin/zsh -d $HOME $USER && \
    chown -R $USER:$USER $HOME

# Switch to the non-root user for the rest of the setup
USER $USER

# 4. Install Oh My Zsh & Starship as the ACTUAL user
RUN sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended && \
    git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

# 5. Configure ZSH (Using a cleaner 'heredoc' style)
RUN <<EOF
echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
echo 'eval "$(starship init zsh)"' >> "$HOME/.zshrc"
echo 'eval "$(uv generate-shell-completion zsh)"' >> "$HOME/.zshrc"
echo 'plugins=(git zsh-autosuggestions)' >> "$HOME/.zshrc"
# Ensure the virtualenv created by uv is automatically used
echo 'source $HOME/.venv/bin/activate 2>/dev/null || true' >> "$HOME/.zshrc"
EOF

# Install Starship (needs sudo or root, so we do it briefly or use a binary copy)
USER root
RUN curl -sS https://starship.rs/install.sh | sh -s -- --yes
USER $USER

ENTRYPOINT []
