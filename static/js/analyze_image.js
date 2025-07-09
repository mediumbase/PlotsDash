async function analyzeImages() {
    console.log("Analyze button clicked!"); // Debugging
    try {
        const response = await fetch('/analyze_images', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const result = await response.json();
        if (response.ok) {
            alert("Analysis successful!\n" + result.message);
        } else {
            alert("Analysis failed!\n" + result.message);
        }
    } catch (error) {
        alert("Error calling the API: " + error.message);
    }
}

// Attach the function to the window object
window.analyzeImages = analyzeImages;