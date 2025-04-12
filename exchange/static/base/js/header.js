const logoutLink = document.getElementById("logout-link");
if (logoutLink) {
  logoutLink.addEventListener("click", function (event) {
    event.preventDefault(); // Prevent default link behavior

    const logoutUrl = this.getAttribute("data-logout-url");
    const csrftoken = getCookie("csrftoken");

    if (!logoutUrl) {
      console.error("Logout URL not found on the link.");
      return; // Stop if the URL isn't set
    }
    if (!csrftoken) {
      console.error("CSRF token not found.");
      // Optionally display an error to the user
      return;
    }

    // --- Use your modal function ---
    modalConfirm({
      title: "Signing out",
      body: "Are you sure you want to sign out?",
      confirmButtonText: "Sign Out",
      confirmButtonClass: "btn-danger", // Use danger style for leaving
      confirmCallback: () => {
        console.log("Confirmed sign out action. Sending request...");

        // Perform the POST request to log out
        fetch(logoutUrl, {
          method: "POST",
          headers: {"X-CSRFToken": csrftoken},
          redirect: "follow",
        })
          .then(response => {
            // Check if the request was successful (status 2xx)
            // or if it resulted in a redirect (often status 0 in opaque redirect)
            if (response.ok || response.redirected || response.status === 0) {
              // Logout successful, the browser might have already been redirected
              // by the response. If not, or to be sure, redirect manually.
              // Redirecting to the URL the server *intended* (response.url)
              // is often best if available and different.
              // Otherwise, redirect to a known safe page like home.
              console.log("Logout request successful. Redirecting...");
              // If response.url is the *final* URL after redirects, use it
              window.location.href = response.url || "/"; // Redirect to final URL or home
            } else {
              // Handle server-side errors (e.g., status 400, 500)
              console.error("Logout failed:", response.status, response.statusText);
              // You could try to read an error message if the server sends one
              response.text().then(text => {
                console.error("Server response:", text);
                // TODO: Display a user-friendly error message
                alert(`Sign out failed: ${response.statusText} (${response.status})`);
              });
            }
          })
          .catch(error => {
            // Handle network errors or other issues with the fetch itself
            console.error("Error during sign out fetch:", error);
            // TODO: Display a user-friendly network error message
            alert("An error occurred while trying to sign out. Please check your connection and try again.");
          });
      },
      cancelCallback: () => {
        console.log("Sign out cancelled.");
      },
    });
    // --- End modal function call ---
  });
}
