(() => {
  function ready(fn) {
    if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", fn);
    else fn();
  }

  function hasSwal() {
    return typeof window.Swal !== "undefined";
  }

  function mapLevelToIcon(level) {
    const l = (level || "").toLowerCase();
    if (l.includes("success")) return "success";
    if (l.includes("error") || l.includes("danger")) return "error";
    if (l.includes("warning")) return "warning";
    return "info";
  }

  function toast(level, title) {
    if (!hasSwal()) return;
    const Toast = window.Swal.mixin({
      toast: true,
      position: "top-end",
      showConfirmButton: false,
      timer: 4000,
      timerProgressBar: true,
    });
    Toast.fire({
      icon: mapLevelToIcon(level),
      title: title || "",
    });
  }

  async function confirmDialog({ title, text, confirmText, cancelText, icon }) {
    if (!hasSwal()) return window.confirm(text || title || "Are you sure?");
    const result = await window.Swal.fire({
      title: title || "Confirm",
      text: text || "",
      icon: icon || "warning",
      showCancelButton: true,
      confirmButtonText: confirmText || "Continue",
      cancelButtonText: cancelText || "Cancel",
      reverseButtons: true,
      focusCancel: true,
    });
    return !!result.isConfirmed;
  }

  // Expose a tiny API
  window.hhUI = {
    toast,
    confirm: confirmDialog,
    alert: (opts) => (hasSwal() ? window.Swal.fire(opts) : window.alert(opts?.text || opts?.title || "")),
  };

  ready(() => {
    // Render Django messages as toasts (if present)
    const root = document.getElementById("django-messages");
    if (root) {
      const nodes = root.querySelectorAll("[data-level][data-text]");
      nodes.forEach((n) => toast(n.getAttribute("data-level"), n.getAttribute("data-text")));
    }

    // SweetAlert confirm for any form/button/link with data-confirm
    // NOTE: we must preventDefault immediately, otherwise the form may submit
    // before the async modal resolves.
    document.addEventListener("click", async (e) => {
      const el = e.target && e.target.closest ? e.target.closest("[data-confirm]") : null;
      if (!el) return;

      e.preventDefault();
      e.stopPropagation();

      const text = el.getAttribute("data-confirm") || "Are you sure?";
      const ok = await confirmDialog({ text, confirmText: el.getAttribute("data-confirm-yes") || "Yes" });
      if (!ok) return;

      // Proceed with the original intent
      if (el.tagName === "A" && el.href) {
        window.location.href = el.href;
        return;
      }

      const form = el.closest("form");
      if (form) {
        if (typeof form.requestSubmit === "function") {
          form.requestSubmit(el);
        } else {
          form.submit();
        }
      }
    });

    // HTMX: show server errors as alerts/toasts
    document.body.addEventListener("htmx:responseError", (evt) => {
      const xhr = evt.detail && evt.detail.xhr;
      const status = xhr ? xhr.status : 0;
      toast("error", `Request failed (${status})`);
    });
  });
})();

