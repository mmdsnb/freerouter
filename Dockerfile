FROM python:3.11-slim

WORKDIR /app

# Copy package files
COPY pyproject.toml README.md ./

# Copy application code
COPY freerouter/ ./freerouter/

# Install the package
RUN pip install --no-cache-dir .

# Expose litellm default port
EXPOSE 4000

# Default command - use the installed CLI
CMD ["freerouter", "start"]
