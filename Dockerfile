# 1. Base image with Python 3.10
FROM python:3.10-slim

# 2. Install system packages needed for SciPy & friends
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# 3. Set working directory
WORKDIR /app

# 4. Copy and install Python dependencies from root requirements.txt
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the entire app folder
COPY app/ ./app

# 6. Expose your Flask port
EXPOSE 5000

# 7. Launch via Gunicorn
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60"]
