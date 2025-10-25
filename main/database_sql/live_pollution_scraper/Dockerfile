# Use a standard Python base image
FROM python:3.9-slim-bullseye

# Install Chromium browser and its matching driver from Debian's repositories
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    # Clean up APT cache
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Run the scraper script
CMD ["python", "main.py"]