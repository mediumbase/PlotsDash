export function startTimeLapse() {
    const button = document.getElementById("start-time-lapse-button");

    // Disable the button and update its text
    if (button) {
        button.disabled = true;
        button.textContent = "Starting...";
    }

    // Send a POST request to the Flask backend
    fetch('/start_time_lapse', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
    })
    .then(response => {
        if (!response.ok) {
            throw new Error("Network response was not ok");
        }
        return response.json();
    })
    .then(data => {
        // Show a success message
        alert(data.message || "Time-lapse started successfully!");
    })
    .catch(error => {
        // Handle errors
        console.error("Error starting time-lapse:", error);
        alert("Failed to start time-lapse: " + error.message);
    })
    .finally(() => {
        // Re-enable the button and reset its text
        if (button) {
            button.disabled = false;
            button.textContent = "Start Time-Lapse";
        }
    });
}

// Attach the function to the window object
window.startTimeLapse = startTimeLapse;