FROM python:3.11-slim

# Install build tools for compiling the C++ binary
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Compile the Huffman C++ binary at image build time
RUN g++ huffman-compression.cpp -O2 -std=c++17 -o huffman-web

EXPOSE 5000

# Use gunicorn for production-style serving
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--workers", "1"]
