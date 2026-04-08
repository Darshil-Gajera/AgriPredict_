FROM python:3.11-slim

WORKDIR /app

# Prevent Python issues
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y build-essential

# Copy requirements
COPY requirements.txt .

# Upgrade pip + increase timeout
RUN pip install --upgrade pip
RUN pip install --no-cache-dir --timeout 1000 -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run Django
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]