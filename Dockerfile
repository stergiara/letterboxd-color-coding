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

# 4. Copy and install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy application code
COPY app ./app
COPY render.yaml .
# If you have other top-level scripts, COPY them too:
COPY main.py .
COPY downloaders.py .
COPY methods.py .
COPY mosaic.py .

# 6. Expose the port your Flask/Gunicorn app listens on
EXPOSE 5000

# 7. Default command to run your app via Gunicorn
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60"]
