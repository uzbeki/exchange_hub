// enable bootstrap tooltip
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

// Global utility for creating dynamic Bootstrap 5 confirmation modals
window.modalConfirm = function (options) {
  // Default options
  const defaults = {
    title: "Confirm", // Modal title
    body: "Are you sure?", // Modal body content, can be HTML
    closeButtonText: "Close", // Close button text
    hasConfirmButton: true, // Modal has a confirm button
    confirmButtonText: "Confirm", // Confirm button text
    confirmButtonClass: "btn-primary", // Confirm button class
    closeCallback: null, // Callback function when modal is closed
    confirmCallback: null, // Callback function when confirm button is clicked
    autoClose: true, // Auto-close the modal after confirm button is clicked
    bodyAsHTML: false, // Set to true if body is HTML
    modalClass: "", // Custom modal classes
    staticModal: false, // New: combines backdrop and keyboard close restrictions
  };

  // Merge provided options with defaults
  const settings = { ...defaults, ...options };

  // Create a unique modal ID to support multiple modals
  const modalId = `bsConfirm-${Date.now()}`;

  // Create modal HTML
  const modalHTML = `
        <div class="modal fade ${settings.modalClass}" id="${modalId}" 
             tabindex="-1" 
             aria-hidden="true"
             data-bs-backdrop="${settings.staticModal ? "static" : "true"}"
             data-bs-keyboard="${!settings.staticModal}">
          <div class="modal-dialog">
            <div class="modal-content">
              <div class="modal-header">
                  <h1 class="modal-title fs-5">${settings.title}</h1>
                  <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
              </div>
              <div class="modal-body">
                ${settings.bodyAsHTML ? settings.body : escapeHTML(settings.body)}
              </div>
              <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
                  ${settings.closeButtonText}
                </button>
                ${
                  settings.hasConfirmButton
                    ? `
                  <button type="button" class="btn ${settings.confirmButtonClass} bs-confirm-action">
                    ${settings.confirmButtonText}
                  </button>`
                    : ""
                }
              </div>
            </div>
          </div>
        </div>
      `;

  // Helper function to escape HTML to prevent XSS when not using bodyAsHTML
  function escapeHTML(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // Append modal to body
  const modalContainer = document.createElement("div");
  modalContainer.innerHTML = modalHTML;
  document.body.appendChild(modalContainer.firstElementChild);

  // Get references to the modal and buttons
  const modalElement = document.getElementById(modalId);
  const confirmButton = modalElement.querySelector(".bs-confirm-action");

  // Create Bootstrap modal instance with custom options
  const modalInstance = new bootstrap.Modal(modalElement, {
    backdrop: settings.staticModal ? "static" : true,
    keyboard: !settings.staticModal,
  });

  // Show the modal
  modalInstance.show();

  // Handle confirm button click
  if (defaults.hasConfirmButton && confirmButton) {
    confirmButton.addEventListener("click", function () {
      // If confirmCallback returns false, prevent modal closing
      if (settings.confirmCallback) {
        const result = settings.confirmCallback();

        // If autoClose is false or callback returns false, don't close
        if (settings.autoClose === false || result === false) {
          return;
        }
      }

      // Close the modal
      modalInstance.hide();
    });
  }

  // Handle modal close event
  modalElement.addEventListener("hidden.bs.modal", function () {
    if (settings.closeCallback) {
      settings.closeCallback();
    }

    // Remove the modal from the DOM
    modalElement.remove();
  });

  // Return the modal instance for advanced control if needed
  return modalInstance;
};

class FocusAwareInterval {
  constructor({ callback, interval = 5_000, delayBeforePause = 0, delayBeforeResume = 0, startImmediately = true }) {
    // Store configuration
    this.callback = callback;
    this.interval = interval;
    this.delayBeforePause = delayBeforePause;
    this.delayBeforeResume = delayBeforeResume;

    // Initialize state and timers
    this.isRunning = false;
    this.timeoutId = null;
    this.pauseTimeout = null;
    this.resumeTimeout = null;

    // Bind methods to maintain context
    this.start = this.start.bind(this);
    this.stop = this.stop.bind(this);
    this.handleVisibilityChange = this.handleVisibilityChange.bind(this);

    // Add visibility change listener
    document.addEventListener("visibilitychange", this.handleVisibilityChange);

    // Start immediately if requested and document is visible
    if (startImmediately && !document.hidden) {
      this.start();
    }
  }

  start() {
    // Prevent starting if already running
    if (this.isRunning) return;
    this.isRunning = true;

    // Clear any pending resume timeout
    clearTimeout(this.resumeTimeout);

    // Schedule the first callback execution after delayBeforeResume
    this.resumeTimeout = setTimeout(() => {
      this.runCallback();
    }, this.delayBeforeResume);
  }

  stop() {
    // Prevent stopping if not running
    if (!this.isRunning) return;

    // Clear any pending pause timeout
    clearTimeout(this.pauseTimeout);

    // Stop the loop after delayBeforePause
    this.pauseTimeout = setTimeout(() => {
      this.isRunning = false;
      clearTimeout(this.timeoutId); // Cancel any scheduled callback
    }, this.delayBeforePause);
  }

  handleVisibilityChange() {
    // Stop when document is hidden, start when visible
    if (document.hidden) {
      this.stop();
    } else {
      this.start();
    }
  }

  runCallback() {
    // Do not proceed if not running
    if (!this.isRunning) return;

    // Execute callback and wait for completion (promise or synchronous)
    Promise.resolve(this.callback()).finally(() => {
      // Schedule next execution only if still running
      if (this.isRunning) {
        this.scheduleNext();
      }
    });
  }

  scheduleNext() {
    // Schedule the next callback execution after the interval
    this.timeoutId = setTimeout(() => {
      this.runCallback();
    }, this.interval);
  }

  destroy() {
    // Stop the loop and clean up
    this.isRunning = false;
    clearTimeout(this.timeoutId);
    clearTimeout(this.pauseTimeout);
    clearTimeout(this.resumeTimeout);
    document.removeEventListener("visibilitychange", this.handleVisibilityChange);
  }
}

function getCookie(name) {
  /* https://docs.djangoproject.com/en/5.1/howto/csrf/#using-csrf-protection-with-ajax */
  let cookieValue = null;
  if (document.cookie && document.cookie !== "") {
    const cookies = document.cookie.split(";");
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      // Does this cookie string begin with the name we want?
      if (cookie.substring(0, name.length + 1) === name + "=") {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
