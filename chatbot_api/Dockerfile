FROM python:3.11-slim

WORKDIR /app

# Prevent Python issues
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# System dependencies (important for ML libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0

# Copy requirements
COPY requirements.txt .

# Upgrade pip + increase timeout
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --timeout 1000 -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8001

# Run FastAPI
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]