# syntax=docker/dockerfile:1

# Python development image with uv
FROM python:3.12-slim

# Create vscode user
RUN groupadd --gid 1000 vscode \
    && useradd --uid 1000 --gid 1000 -m -s /bin/bash vscode \
    && apt-get update && apt-get install -y \
    git \
    sudo \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages for notebook
RUN pip install --no-cache-dir \
    ipykernel \
    pandas

USER vscode

# Install Playwright MCP browser (Chrome is not available on ARM64)
RUN npx @playwright/mcp install-browser chrome-for-testing

USER root
RUN npx playwright install-deps chromium
USER vscode

# Install uv for vscode user
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/home/vscode/.local/bin:$PATH"

# Install Claude Code
RUN curl -fsSL https://claude.ai/install.sh | bash

WORKDIR /workspaces/grand-oral

# Start Flink cluster as flink user when container starts
CMD [ "/bin/sh" "-c" "while sleep 1000; do :; done" ]