# Use an official Python 3.10 image
FROM python:3.10-slim

# Install system dependencies for SciPy, scikit-image, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    gfortran \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and switch to the app directory
WORKDIR /app

# Copy and install Python dependencies
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire app folder (with all .py files inside)
COPY app/ ./app

# Expose the Flask port
EXPOSE 5000

# Start the app
CMD ["gunicorn", "app.main:app", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "60"]
