FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    scons \
    swig \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY upload/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY upload/src ./
COPY upload/start.py ./start.py

CMD ["python", "-u", "start.py"]
