# UV-MCP Docker Image
# Multi-stage build for minimal image size

# =============================================================================
# Build stage
# =============================================================================
FROM python:3.11-slim as builder

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy project files (README.md is required by pyproject.toml)
COPY pyproject.toml uv.lock README.md ./
COPY src/ ./src/

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev

# =============================================================================
# Runtime stage
# =============================================================================
FROM python:3.11-slim as runtime

# Labels
LABEL org.opencontainers.image.title="UV-MCP"
LABEL org.opencontainers.image.description="MCP server for uv - environment diagnostics, repair, and dependency management"
LABEL org.opencontainers.image.version="0.5.0"
LABEL org.opencontainers.image.source="https://github.com/saadmanrafat/uv-mcp"
LABEL org.opencontainers.image.licenses="MIT"

# Install uv in runtime image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY src/ ./src/
COPY pyproject.toml ./

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from uv_mcp.uv_utils import check_uv_available; assert check_uv_available()[0]" || exit 1

# Default command - run the MCP server
CMD ["python", "-m", "uv_mcp.server"]

# =============================================================================
# Development stage (optional)
# =============================================================================
FROM runtime as development

# Switch back to root to install dev dependencies
USER root

# Copy test files
COPY tests/ ./tests/
COPY test_tools.py ./

# Install dev dependencies
RUN uv sync --frozen

# Switch back to non-root user
USER appuser

# Development command
CMD ["pytest", "tests/", "-v"]
