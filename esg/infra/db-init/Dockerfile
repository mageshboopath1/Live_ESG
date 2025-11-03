# Extend pgvector image with Python and UV for running seed scripts
FROM pgvector/pgvector:pg15

# Install Python 3, pip, and UV
RUN apt-get update && \
    apt-get install -y python3 python3-pip python3-venv curl && \
    curl -LsSf https://astral.sh/uv/install.sh | sh && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Add uv to PATH
ENV PATH="/root/.local/bin:$PATH"

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with UV
RUN uv sync --frozen

# Add .venv to PATH so Python can find installed packages
ENV PATH="/.venv/bin:$PATH"

# The db-init scripts will be mounted to /docker-entrypoint-initdb.d by docker-compose
