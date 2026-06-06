import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_file

BASE_DIR = Path(__file__).resolve().parent
CPP_SOURCE = BASE_DIR / "huffman-compression.cpp"
BINARY_NAME = "huffman-web.exe" if os.name == "nt" else "huffman-web"
BINARY_PATH = BASE_DIR / BINARY_NAME
MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_CONTENT_LENGTH


def ensure_binary() -> tuple[bool, str]:
    if BINARY_PATH.exists():
        return True, ""

    compiler = shutil.which("g++")
    if not compiler:
        return False, "g++ not found. Install a C++ compiler before running compression."

    build_cmd = [compiler, str(CPP_SOURCE), "-O2", "-std=c++17", "-o", str(BINARY_PATH)]
    try:
        completed = subprocess.run(build_cmd, capture_output=True, text=True, check=True)
        if completed.returncode == 0:
            return True, ""
    except subprocess.CalledProcessError as exc:
        details = exc.stderr.strip() or exc.stdout.strip() or "Unknown compiler error"
        return False, f"Failed to build Huffman binary: {details}"

    return False, "Failed to build Huffman binary for unknown reasons."


def run_huffman(mode: str, uploaded_file) -> tuple[bool, str, Path | None, str | None]:
    ok, error = ensure_binary()
    if not ok:
        return False, error, None, None

    action = "-c" if mode == "compress" else "-dc"

    with tempfile.TemporaryDirectory(prefix="huffman-web-") as tmpdir:
        tmp_path = Path(tmpdir)
        original_name = Path(uploaded_file.filename).name
        if not original_name:
            return False, "Please choose a valid file.", None, None

        input_path = tmp_path / original_name
        uploaded_file.save(input_path)

        try:
            completed = subprocess.run(
                [str(BINARY_PATH), action, input_path.name],
                cwd=tmp_path,
                capture_output=True,
                text=True,
                check=True,
            )
        except subprocess.CalledProcessError as exc:
            details = exc.stderr.strip() or exc.stdout.strip() or "Compression command failed"
            return False, details, None, None

        if mode == "compress":
            output_path = tmp_path / f"{input_path.name}.abiz"
            # use base name without original extension for a cleaner download name
            download_name = f"{input_path.stem}.abiz"
        else:
            if not input_path.name.endswith(".abiz"):
                return False, "For decompression, upload a .abiz file.", None, None
            # the C++ decompressor writes a file named 'output' + original_name_without_.abiz
            output_name = f"output{input_path.name[:-5]}"
            output_path = tmp_path / output_name
            # present a cleaner filename to the user by removing the auto 'output' prefix
            download_name = input_path.name[:-5]

        if not output_path.exists():
            stdout = completed.stdout.strip()
            stderr = completed.stderr.strip()
            details = "\n".join(filter(None, [stdout, stderr])) or "No output generated."
            return False, f"Huffman process finished but output file was not created. {details}", None, None

        # Move output to a persistent temp file that survives after TemporaryDirectory cleanup.
        final_temp = Path(tempfile.mkdtemp(prefix="huffman-result-")) / download_name
        shutil.copy2(output_path, final_temp)
        return True, "", final_temp, download_name


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/process")
def process_file():
    mode = request.form.get("mode", "compress").strip().lower()
    uploaded_file = request.files.get("file")

    if mode not in {"compress", "decompress"}:
        return jsonify({"error": "Invalid mode. Use compress or decompress."}), 400

    if not uploaded_file or uploaded_file.filename == "":
        return jsonify({"error": "Please select a file."}), 400

    ok, error, output_path, download_name = run_huffman(mode, uploaded_file)
    if not ok:
        return jsonify({"error": error}), 400

    response = send_file(output_path, as_attachment=True, download_name=download_name)

    @response.call_on_close
    def cleanup():
        try:
            parent = output_path.parent
            if output_path.exists():
                output_path.unlink()
            if parent.exists():
                parent.rmdir()
        except OSError:
            pass

    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=True)
