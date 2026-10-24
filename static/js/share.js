(() => {
  const share = window.QUICKSHARE_SHARE;
  if (!share) return;

  const remainingEl = document.getElementById("remaining");
  const statusLine = document.getElementById("status-line");
  const storageKey = `quickshare-autodownload:${share.token}`;

  function formatCountdown(ms) {
    const total = Math.max(0, Math.ceil(ms / 1000));
    const minutes = String(Math.floor(total / 60)).padStart(2, "0");
    const seconds = String(total % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  }

  function tick() {
    const ms = new Date(share.expiresAt).getTime() - Date.now();
    remainingEl.textContent = formatCountdown(ms);
    if (ms <= 0) {
      window.location.replace("/");
    }
  }

  tick();
  setInterval(tick, 250);

  function startDownloadOnce() {
    if (sessionStorage.getItem(storageKey)) {
      statusLine.textContent = "If the download did not start, use the button below.";
      return;
    }
    sessionStorage.setItem(storageKey, "1");
    const frame = document.createElement("iframe");
    frame.style.display = "none";
    frame.src = share.downloadUrl;
    document.body.appendChild(frame);
    statusLine.textContent = "Download started. Use the button below if your browser blocked it.";
  }

  startDownloadOnce();
  if (window.lucide) window.lucide.createIcons();
})();
