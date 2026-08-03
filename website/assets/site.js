document.querySelectorAll("[data-copy-target]").forEach((button) => {
  button.addEventListener("click", async () => {
    const command = document.querySelector(button.dataset.copyTarget);
    if (!command) return;

    const originalLabel = button.textContent;
    try {
      await navigator.clipboard.writeText(command.textContent.trim());
      button.textContent = "Copied";
    } catch {
      button.textContent = "Select command";
    }

    window.setTimeout(() => {
      button.textContent = originalLabel;
    }, 1800);
  });
});
