const form = document.getElementById("compressForm");
const fileInput = document.getElementById("fileInput");
const fileName = document.getElementById("fileName");
const statusEl = document.getElementById("status");
const dropzone = document.getElementById("dropzone");
const actionButtons = form.querySelectorAll("button[type='submit']");

let currentMode = "compress";

function setStatus(message, type = "") {
  statusEl.textContent = message;
  statusEl.className = `status ${type}`.trim();
}

function setBusy(isBusy) {
  actionButtons.forEach((btn) => {
    btn.disabled = isBusy;
  });
}

fileInput.addEventListener("change", () => {
  const file = fileInput.files[0];
  fileName.textContent = file ? file.name : "No file selected";
});

dropzone.addEventListener("dragover", (event) => {
  event.preventDefault();
  dropzone.classList.add("drag");
});

["dragleave", "dragend"].forEach((name) => {
  dropzone.addEventListener(name, () => dropzone.classList.remove("drag"));
});

dropzone.addEventListener("drop", (event) => {
  event.preventDefault();
  dropzone.classList.remove("drag");
  const file = event.dataTransfer.files[0];
  if (file) {
    const transfer = new DataTransfer();
    transfer.items.add(file);
    fileInput.files = transfer.files;
    fileName.textContent = file.name;
  }
});

actionButtons.forEach((button) => {
  button.addEventListener("click", () => {
    currentMode = button.dataset.mode;
  });
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const file = fileInput.files[0];
  if (!file) {
    setStatus("Please choose a file first.", "error");
    return;
  }

  setBusy(true);
  setStatus(`${currentMode === "compress" ? "Compressing" : "Decompressing"} file...`);

  try {
    const payload = new FormData();
    payload.append("file", file);
    payload.append("mode", currentMode);

    const response = await fetch("/api/process", {
      method: "POST",
      body: payload,
    });

    if (!response.ok) {
      let errorMessage = "Request failed.";
      try {
        const details = await response.json();
        errorMessage = details.error || errorMessage;
      } catch {
        // Keep generic message if server does not return JSON.
      }
      throw new Error(errorMessage);
    }

    const blob = await response.blob();
    const baseName = file.name.replace(/\.[^/.]+$/, '');
    const fallbackName = currentMode === "compress" ? `${baseName}.abiz` : `${file.name.replace(/\.abiz$/i, '')}`;
    const disposition = response.headers.get("Content-Disposition") || "";
    const match = disposition.match(/filename="?([^\";]+)"?/i);
    const downloadName = match?.[1] || fallbackName;

    const url = window.URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = downloadName;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    window.URL.revokeObjectURL(url);

    setStatus("Done. Your download has started.", "success");
  } catch (error) {
    setStatus(error.message || "Unexpected error", "error");
  } finally {
    setBusy(false);
  }
});
