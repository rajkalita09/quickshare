(() => {
  const cfg = window.QUICKSHARE || { maxUploadBytes: 26214400, expirySeconds: 600 };
  const form = document.getElementById("upload-form");
  const fileInput = document.getElementById("file-input");
  const dropzone = document.getElementById("dropzone");
  const chooseBtn = document.getElementById("choose-btn");
  const uploadBtn = document.getElementById("upload-btn");
  const uploadCard = document.getElementById("upload-card");
  const resultCard = document.getElementById("result-card");
  const selectedWrap = document.getElementById("selected-file");
  const selectedName = document.getElementById("selected-name");
  const selectedSize = document.getElementById("selected-size");
  const removeFile = document.getElementById("remove-file");
  const progressPanel = document.getElementById("progress-panel");
  const progressBar = document.getElementById("progress-bar");
  const progressPercent = document.getElementById("progress-percent");
  const progressStatus = document.getElementById("progress-status");
  const progressFilename = document.getElementById("progress-filename");
  const errorMessage = document.getElementById("error-message");
  const maxSizeLabel = document.getElementById("max-size-label");
  const shareUrl = document.getElementById("share-url");
  const qrImage = document.getElementById("qr-image");
  const resultName = document.getElementById("result-name");
  const resultSize = document.getElementById("result-size");
  const copyLink = document.getElementById("copy-link");
  const copyLabel = document.getElementById("copy-label");
  const downloadQr = document.getElementById("download-qr");
  const anotherFile = document.getElementById("another-file");
  const countdownEl = document.getElementById("countdown");
  const ringFg = document.getElementById("ring-fg");
  const resultActive = document.getElementById("result-active");
  const resultExpired = document.getElementById("result-expired");

  let selected = null;
  let uploading = false;
  let countdownTimer = null;
  let currentShare = null;
  const circumference = 2 * Math.PI * 42;

  maxSizeLabel.textContent = formatSize(cfg.maxUploadBytes);

  function formatSize(bytes) {
    const units = ["B", "KB", "MB", "GB"];
    let size = bytes;
    let unit = 0;
    while (size >= 1024 && unit < units.length - 1) {
      size /= 1024;
      unit += 1;
    }
    if (unit === 0) return `${bytes} B`;
    const rounded = Math.round(size * 10) / 10;
    const label = Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1);
    return `${label} ${units[unit]}`;
  }

  function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.remove("hidden");
    uploadCard.dataset.state = "error";
  }

  function clearError() {
    errorMessage.classList.add("hidden");
    errorMessage.textContent = "";
  }

  function refreshIcons() {
    if (window.lucide) window.lucide.createIcons();
  }

  function setSelected(file) {
    clearError();
    if (!file) {
      selected = null;
      fileInput.value = "";
      selectedWrap.classList.add("hidden");
      uploadBtn.disabled = true;
      uploadCard.dataset.state = "idle";
      return;
    }
    if (file.size <= 0) {
      showError("Empty files are not allowed.");
      return;
    }
    if (file.size > cfg.maxUploadBytes) {
      showError(`File is too large. Maximum size is ${formatSize(cfg.maxUploadBytes)}.`);
      return;
    }
    selected = file;
    selectedName.textContent = file.name;
    selectedSize.textContent = formatSize(file.size);
    selectedWrap.classList.remove("hidden");
    uploadBtn.disabled = false;
    uploadCard.dataset.state = "idle";
    refreshIcons();
  }

  function openPicker() {
    fileInput.click();
  }

  dropzone.addEventListener("click", openPicker);
  chooseBtn.addEventListener("click", (event) => {
    event.stopPropagation();
    openPicker();
  });
  dropzone.addEventListener("keydown", (event) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openPicker();
    }
  });
  fileInput.addEventListener("change", () => {
    if (fileInput.files[0]) setSelected(fileInput.files[0]);
  });
  removeFile.addEventListener("click", () => setSelected(null));

  ["dragenter", "dragover"].forEach((type) => {
    dropzone.addEventListener(type, (event) => {
      event.preventDefault();
      uploadCard.dataset.state = "drag";
    });
  });
  ["dragleave", "drop"].forEach((type) => {
    dropzone.addEventListener(type, (event) => {
      event.preventDefault();
      if (type === "drop") {
        const file = event.dataTransfer.files[0];
        if (file) setSelected(file);
      }
      uploadCard.dataset.state = selected ? "idle" : "idle";
    });
  });

  function setProgress(percent, known) {
    const value = known ? Math.max(0, Math.min(99, percent)) : percent;
    progressBar.style.width = `${value}%`;
    progressPercent.textContent = known ? `${value}%` : "Uploading…";
    progressPanel.querySelector(".progress-track").setAttribute("aria-valuenow", String(value));
  }

  function uploadFile(file) {
    if (uploading) return;
    uploading = true;
    uploadBtn.disabled = true;
    chooseBtn.disabled = true;
    fileInput.disabled = true;
    clearError();
    progressPanel.classList.remove("hidden");
    progressFilename.textContent = file.name;
    progressStatus.textContent = "Uploading…";
    uploadCard.dataset.state = "uploading";
    setProgress(0, true);

    const xhr = new XMLHttpRequest();
    const body = new FormData();
    body.append("file", file);

    xhr.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) {
        const percent = Math.round((event.loaded / event.total) * 100);
        // Never paint a fake 100% before the server confirms success.
        setProgress(percent === 100 ? 99 : percent, true);
      } else {
        progressStatus.textContent = "Uploading…";
      }
    });

    xhr.addEventListener("load", () => {
      uploading = false;
      chooseBtn.disabled = false;
      fileInput.disabled = false;
      let payload = {};
      try {
        payload = JSON.parse(xhr.responseText || "{}");
      } catch (_err) {
        payload = {};
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        progressStatus.textContent = "Upload complete";
        progressBar.style.width = "100%";
        progressPercent.textContent = "100%";
        showResult(payload);
      } else {
        uploadBtn.disabled = false;
        showError(payload.error || "Upload failed. Please try again.");
      }
    });

    xhr.addEventListener("error", () => {
      uploading = false;
      uploadBtn.disabled = false;
      chooseBtn.disabled = false;
      fileInput.disabled = false;
      showError("Network error. Check your connection and try again.");
    });

    xhr.open("POST", "/api/upload");
    xhr.send(body);
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    if (!selected) {
      showError("Please choose a file to upload.");
      return;
    }
    uploadFile(selected);
  });

  function remainingMs(expiresAt) {
    return new Date(expiresAt).getTime() - Date.now();
  }

  function formatCountdown(ms) {
    const total = Math.max(0, Math.ceil(ms / 1000));
    const minutes = String(Math.floor(total / 60)).padStart(2, "0");
    const seconds = String(total % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  }

  function tickCountdown() {
    if (!currentShare) return;
    const ms = remainingMs(currentShare.expires_at);
    countdownEl.textContent = formatCountdown(ms);
    const total = (currentShare.expiry_seconds || cfg.expirySeconds) * 1000;
    const offset = circumference - Math.max(0, Math.min(1, ms / total)) * circumference;
    ringFg.style.strokeDasharray = String(circumference);
    ringFg.style.strokeDashoffset = String(offset);
    if (ms <= 0) {
      clearInterval(countdownTimer);
      resultActive.classList.add("hidden");
      resultExpired.classList.remove("hidden");
      shareUrl.value = "";
      qrImage.removeAttribute("src");
      refreshIcons();
    }
  }

  function showResult(payload) {
    currentShare = payload;
    uploadCard.classList.add("hidden");
    resultCard.classList.remove("hidden");
    resultActive.classList.remove("hidden");
    resultExpired.classList.add("hidden");
    shareUrl.value = payload.share_url;
    qrImage.src = payload.qr_url;
    resultName.textContent = payload.filename;
    resultSize.textContent = formatSize(payload.size);
    if (countdownTimer) clearInterval(countdownTimer);
    tickCountdown();
    countdownTimer = setInterval(tickCountdown, 250);
    refreshIcons();
  }

  copyLink.addEventListener("click", async () => {
    const value = shareUrl.value;
    if (!value) return;
    try {
      await navigator.clipboard.writeText(value);
    } catch (_err) {
      shareUrl.select();
      document.execCommand("copy");
    }
    copyLabel.textContent = "Copied";
    setTimeout(() => {
      copyLabel.textContent = "Copy Link";
    }, 1500);
  });

  downloadQr.addEventListener("click", async () => {
    if (!currentShare) return;
    const response = await fetch(currentShare.qr_url);
    if (!response.ok) return;
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "quickshare-qr.png";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
  });

  anotherFile.addEventListener("click", () => {
    if (countdownTimer) clearInterval(countdownTimer);
    currentShare = null;
    setSelected(null);
    progressPanel.classList.add("hidden");
    setProgress(0, true);
    resultCard.classList.add("hidden");
    uploadCard.classList.remove("hidden");
    uploadBtn.disabled = true;
  });
})();
