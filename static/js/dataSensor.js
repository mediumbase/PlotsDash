import { endpoints } from './routing.js';

// Fetch and display sensor data
export async function fetchSensorData() {
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