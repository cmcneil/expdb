FROM mcr.microsoft.com/devcontainers/python:1-3.12-bullseye

ENV PYTHONUNBUFFERED 1

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gpg \
    python3-psycopg2 \
    python3-opencv \
    ffmpeg

# Install Google Cloud SDK
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list \
    && curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg \
    && apt-get update \
    && apt-get install -y google-cloud-cli

# Create and activate virtual environment
RUN uv venv /workspaces/venv

# Add venv to PATH
ENV PATH="/workspaces/venv/bin:$PATH"



