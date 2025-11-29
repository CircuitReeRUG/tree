FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ /app/

# Default command (can be overridden in docker-compose)
CMD ["python", "-u", "start.py"]
