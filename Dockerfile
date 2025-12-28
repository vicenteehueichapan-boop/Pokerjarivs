FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (including potential solver dependencies)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Environment variables
ENV PYTHONPATH=/app
ENV DB_URL=sqlite:///poker_brain_simulation.db

# Default command
CMD ["python3", "scripts/train_loop.py"]
