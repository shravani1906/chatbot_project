document.addEventListener("DOMContentLoaded", function() {
    const chatForm = document.querySelector("form");
    const chatInput = document.querySelector(".chat-input");
    const chatLog = document.querySelector(".chat-log");

    // Scroll chat log to bottom
    function scrollToBottom() {
        chatLog.scrollTop = chatLog.scrollHeight;
    }

    // Prevent form submission if input is empty
    chatForm.addEventListener("submit", function(event) {
        if (chatInput.value.trim() === "") {
            event.preventDefault();
        }
    });

    // Automatically scroll to bottom on new message
    scrollToBottom();
});
