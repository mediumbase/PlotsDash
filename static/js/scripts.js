// Configuration for API endpoints
const endpoints = {
    growthRate: "/growth_rate",
    seasonalStatus: "/seasonal_status",
    harvestScheduler: "/harvest_scheduler",
    growthGraph: "/growth_graph",
    sensorData: "/sensor_data",
    inferenceData: "/inference_data",
};

// Function to update the time and date
function updateDateTime() {
    const now = new Date();
    const datetimeElement = document.getElementById("datetime");
    datetimeElement.textContent = now.toLocaleString();
}

// Update the time and date every second
setInterval(updateDateTime, 1000);
updateDateTime(); // Initial call

// Reusable function to fetch and display data in a table
async function fetchData(url, tableId, rowTemplate) {
    const tableBody = document.getElementById(tableId);
    tableBody.innerHTML = `<tr><td colspan="4">Loading...</td></tr>`; // Show loading indicator

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        tableBody.innerHTML = ""; // Clear loading indicator
        data.forEach((row) => {
            const tr = document.createElement("tr");
            tr.innerHTML = rowTemplate(row);
            tableBody.appendChild(tr);
        });
    } catch (error) {
        console.error(`Error fetching data from ${url}:`, error);
        tableBody.innerHTML = `<tr><td colspan="4">Failed to load data. Please try again later.</td></tr>`;
    }
}

// Fetch and display sensor data
async function fetchSensorData() {
    try {
        const response = await fetch(endpoints.sensorData);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();

        // Update system monitoring data
        document.getElementById("cpu-usage").textContent = `${data.cpu_usage.toFixed(2)}%`;
        document.getElementById("ram-usage").textContent = `${data.ram_usage.toFixed(2)}%`;
        document.getElementById("storage-usage").textContent = `${data.storage_usage.toFixed(2)}%`;

        // Update IP address
        document.getElementById("ip-address").textContent = `IP: ${data.ip_address}`;

        // Update sensor data
        document.getElementById("analog-value").textContent = `${data.analog_value !== null ? data.analog_value : "N/A"}`;
        document.getElementById("color-red").textContent = `${data.color_red !== null ? data.color_red : "N/A"}`;
        document.getElementById("accel-x").textContent = `${data.accel_x !== null ? data.accel_x.toFixed(2) : "N/A"}`;
        document.getElementById("pressure").textContent = `${data.pressure !== null ? data.pressure.toFixed(2) : "N/A"}`;
        document.getElementById("temperature-sht").textContent = `${data.temperature_sht !== null ? data.temperature_sht.toFixed(2) : "N/A"}`;
    } catch (error) {
        console.error("Error fetching sensor data:", error);
    }
}

// Fetch and display growth rate data
function fetchGrowthRateData() {
    fetchData(endpoints.growthRate, "growth-rate-table-body", (row) => `
        <td>${row.plant_name}</td>
        <td>${row.rate}</td>
        <td>${row.height}</td>
        <td>${row.time_after_planting}</td>
    `);
}

// Fetch and display growth graph
async function fetchGrowthGraph() {
    try {
        const response = await fetch(endpoints.growthGraph);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();

        const graphImg = document.getElementById("growth-graph");
        if (data.image) {
            graphImg.src = `data:image/png;base64,${data.image}`;
        } else {
            graphImg.src = "https://via.placeholder.com/400x200?text=Graph+Not+Available";
        }
    } catch (error) {
        console.error("Error fetching growth graph:", error);
        const graphImg = document.getElementById("growth-graph");
        graphImg.src = "https://via.placeholder.com/400x200?text=Error+Loading+Graph";
    }
}

// Fetch and display seasonal status
function fetchSeasonalStatus() {
    fetchData(endpoints.seasonalStatus, "seasonal-status-table-body", (row) => `
        <td>${row.plant_name}</td>
        <td>${row.start_date}</td>
        <td>${row.current_stage}</td>
    `);
}

// Fetch and display harvest scheduler
function fetchHarvestScheduler() {
    fetchData(endpoints.harvestScheduler, "harvest-scheduler-table-body", (row) => `
        <td>${row.plant_name}</td>
        <td>${row.predicted_harvest_date}</td>
    `);
}

// Function to fetch an image of the detected species
async function fetchSpeciesImage(speciesName) {
    try {
        const response = await fetch(
            `https://en.wikipedia.org/w/api.php?action=query&titles=${encodeURIComponent(speciesName)}&prop=pageimages&format=json&pithumbsize=100&origin=*`
        );
        const data = await response.json();
        const pages = data.query.pages;
        const pageId = Object.keys(pages)[0];
        const imageUrl = pages[pageId].thumbnail?.source;

        return imageUrl || "https://via.placeholder.com/50"; // Fallback to a placeholder if no image is found
    } catch (error) {
        console.error("Error fetching species image:", error);
        return "https://via.placeholder.com/50"; // Fallback to a placeholder on error
    }
}

// Fetch and display detection insights
async function updateDetectionData() {
    try {
        const response = await fetch(endpoints.inferenceData);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();

        // Find the detection with the highest confidence score
        const highestConfidenceDetection = data.reduce((prev, current) =>
            prev.confidence > current.confidence ? prev : current
        );

        // Highlight the detection insights box if confidence > 30
        const detectionInsightsBox = document.getElementById("detection-insights-box");
        if (highestConfidenceDetection.confidence > 30) {
            detectionInsightsBox.classList.add("highlight");
        } else {
            detectionInsightsBox.classList.remove("highlight");
        }

        // Fetch an image of the detected species
        const imageUrl = await fetchSpeciesImage(highestConfidenceDetection.label);

        // Create the insight card
        const insightCard = `
            <div class="insight-card">
                <img src="${imageUrl}" alt="${highestConfidenceDetection.label}">
                <div class="content">
                    <h4>Breaking: ${highestConfidenceDetection.label} detected with ${highestConfidenceDetection.confidence.toFixed(2)} confidence!</h4>
                    <p>Did you know? ${highestConfidenceDetection.label} is a fascinating species!</p>
                    <p>Stay tuned for more updates on detected objects in your environment.</p>
                </div>
            </div>
        `;

        // Update the Detection Insights section
        const detectionInsights = document.getElementById("detection-insights");
        detectionInsights.innerHTML = insightCard;

        // Update the Last 5 Detections table
        const detectionsTableBody = document.getElementById("detections-table-body");
        detectionsTableBody.innerHTML = data
            .map(
                (detection) => `
                <tr>
                    <td>${detection.category}</td>
                    <td class="label-small-font">${detection.label}</td>
                    <td>${detection.confidence.toFixed(2)}</td>
                </tr>
            `
            )
            .join(""); // Concatenate the array into a single string
    } catch (error) {
        console.error("Error updating detection data:", error);
    }
}

// Function to take a snapshot of the live feed
function takeSnapshot() {
    const videoFeed = document.querySelector(".video-feed img, .video-feed video");
    const canvas = document.createElement("canvas");
    canvas.width = videoFeed.videoWidth || videoFeed.width;
    canvas.height = videoFeed.videoHeight || videoFeed.height;
    const context = canvas.getContext("2d");
    context.drawImage(videoFeed, 0, 0, canvas.width, canvas.height);

    const link = document.createElement("a");
    link.download = "snapshot.png";
    link.href = canvas.toDataURL("image/png");
    link.click();
}

// Periodically fetch and update data
setInterval(fetchSensorData, 2000);
setInterval(fetchGrowthRateData, 5000);
setInterval(fetchGrowthGraph, 5000);
setInterval(fetchSeasonalStatus, 10000);
setInterval(fetchHarvestScheduler, 10000);
setInterval(updateDetectionData, 2000);

// Initial data fetch
fetchSensorData();
fetchGrowthRateData();
fetchGrowthGraph();
fetchSeasonalStatus();
fetchHarvestScheduler();
updateDetectionData();