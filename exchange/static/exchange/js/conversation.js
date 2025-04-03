document.getElementById("deleteChatButton").addEventListener("click", e => {
  console.log("deleteChatButton click");
  const id = e.target.dataset.id;

  modalConfirm({
    title: "Are you sure to delete this chat?",
    body: "This action cannot be undone.",
    confirmButtonText: "Delete",
    confirmButtonClass: "btn-danger",
    confirmCallback: () => {
      console.log("Confirmed delete action");
      // send DELETE request to the server /exchange/conversations/<id>/delete/, follow success redirects
      fetch(`/exchange/conversations/${id}/delete/`, {
        method: "POST",
        headers: {
          "X-CSRFToken": getCookie("csrftoken"),
          "Content-Type": "application/json",
        },
      })
        .then(r => {
          r.json().then(data=>{
            if (r.ok) {
              console.log("Delete successful:", data);
              // Redirect to the conversations page
              window.location.href = data.redirect_url;
            }else {
              console.error("Delete failed:", data);
              // Show error message to the user
            }
          })
        })
        .catch(error => {
          console.error("Error during fetch:", error);
        });
    },
  });
});
document.getElementById("shareContactButton").addEventListener("click", e => {
  console.log("shareContactButton click");
});
document.getElementById("blockUserButton").addEventListener("click", e => {
  console.log("blockUserButton click");
});
document.getElementById("reportUserButton").addEventListener("click", e => {
  console.log("reportUserButton click");
});
document.getElementById("muteNotificationsButton").addEventListener("click", e => {
  console.log("muteNotificationsButton click");
});
document.getElementById("unmuteNotificationsButton").addEventListener("click", e => {
  console.log("unmuteNotificationsButton click");
});
