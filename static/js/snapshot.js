function takeSnapshot() {
    const videoFeed = document.querySelector(".video-feed img, .video-feed video");
    if (!videoFeed) {
        console.error("Video feed not found!");
        alert("Error: Video feed not found!");
        return;
    }

    // Create a canvas element
    const canvas = document.createElement("canvas");
    canvas.width = videoFeed.videoWidth || videoFeed.width;
    canvas.height = videoFeed.videoHeight || videoFeed.height;
    const context = canvas.getContext("2d");

    // Draw the current frame from the video feed onto the canvas
    context.drawImage(videoFeed, 0, 0, canvas.width, canvas.height);

    // Generate a timestamp for the filename
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const filename = `snapshot_${timestamp}.png`;

    // Create a download link
    const link = document.createElement("a");
    link.download = filename;
    link.href = canvas.toDataURL("image/png");
    link.click();

    // Provide feedback to the user
    alert("Snapshot captured and downloaded!");
    console.log(`Snapshot captured and saved as ${filename}`);
}

// Attach the function to the window object
window.takeSnapshot = takeSnapshot;