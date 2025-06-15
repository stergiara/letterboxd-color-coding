FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install dependencies from root requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app

EXPOSE 5000

CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60"]
