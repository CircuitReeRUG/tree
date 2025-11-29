FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
COPY src/requirements.txt ./src/
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r src/requirements.txt

# Copy source code
COPY src/ .

# Expose Flask port
EXPOSE 5000

# Run Flask app
CMD ["python", "-u", "webapp/app.py"]