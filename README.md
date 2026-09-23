# Huffman Compression

This project contains a C++ Huffman compression engine, a command-line interface, and a Flask web application packaged for Docker deployment. The maintained source and web application live in [`huffman-compressor/`](huffman-compressor/); this is the only implementation directory.

## How it works

The compressor counts byte frequencies, builds a binary Huffman tree, and writes the generated codes plus padding metadata into an `.abiz` file. Decompression reads that metadata to rebuild the tree and restore the original bytes.

Huffman coding is most useful for text and other data with repeated byte patterns. Already-compressed formats such as MP3, MP4, PDF, and DOCX may see little or no size reduction.

## Command-line interface

From the application directory, compile the engine with a C++17 compiler:

```bash
cd huffman-compressor
g++ huffman-compression.cpp -O2 -std=c++17 -o huffman
```

Compress a file. This creates `<filename>.abiz`:

```bash
./huffman -c input.txt
```

Decompress an `.abiz` file. This creates `output<original-filename>`:

```bash
./huffman -dc input.txt.abiz
```

On Windows, run the corresponding `huffman.exe` commands. The web app compiles the same source automatically when needed.

## Flask web interface

The browser interface supports both workflows:

- Upload a file to compress it and download the resulting `.abiz` file.
- Upload an `.abiz` file to decompress it and download the restored file.

Run locally with Python 3.10+ and `g++` installed:

```bash
cd huffman-compressor
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open <http://localhost:5000>. For a production-style local server, use:

```bash
gunicorn app:app --bind 0.0.0.0:5000 --workers 1
```

## Docker deployment

The Dockerfile installs the C++ build toolchain, compiles the engine, installs the Flask dependencies, and serves the app with Gunicorn.

Build and run from the repository root:

```bash
docker build -t huffman-compressor:latest ./huffman-compressor
docker run --rm -p 5000:5000 huffman-compressor:latest
```

Then open <http://localhost:5000>. The image exposes port `5000`.

## CI/CD

GitHub Actions is configured in [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml). On pushes and pull requests it compiles the C++ engine and verifies a compress/decompress byte-for-byte round trip. On pushes to `main`, it also builds and pushes the Docker image.

Configure these repository secrets before enabling the image push:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

The published image name is `${DOCKERHUB_USERNAME}/huffman-compression`.
