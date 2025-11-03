# ============================================================================
# Stage 1: Builder - Install UV and dependencies
# ============================================================================
FROM apache/airflow:2.10.4-python3.12 AS builder

USER root

# Install system dependencies and UV
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install UV
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:$PATH"

# Create working directory
WORKDIR /build

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies using UV
# Note: We use --no-dev to exclude development dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# ============================================================================
# Stage 2: Runtime - Final Airflow image
# ============================================================================
FROM apache/airflow:2.10.4-python3.12

USER root

# Install runtime system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Copy installed packages from builder
# Note: Airflow base image already has packages in /home/airflow/.local
# We install additional packages on top
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /home/airflow/.local/lib/python3.12/site-packages/
COPY --from=builder /usr/local/bin/ /home/airflow/.local/bin/

# Copy DAGs and plugins
COPY dags/ /opt/airflow/dags/
COPY plugins/ /opt/airflow/plugins/

# Set working directory
WORKDIR /opt/airflow

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
