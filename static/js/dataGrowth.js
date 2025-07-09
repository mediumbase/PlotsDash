import { endpoints } from './routing.js';
import { fetchData } from './utils.js';

// Fetch and display growth rate data
export function fetchGrowthRateData() {
    fetchData(endpoints.growthRate, 'growth-rate-table-body', row => `
        <td>${row.plant_name}</td>
        <td>${row.rate}</td>
        <td>${row.height}</td>
        <td>${row.time_after_planting}</td>
    `);
}

// Fetch and display growth graph
export function fetchGrowthGraph() {
    fetch('/growth_graph')  // or '/stored_growth_graph'
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log("Graph Data:", data);  // Debugging: Log the received data
            const graphImg = document.getElementById('growth-graph');
            if (data.image) {
                graphImg.src = `data:image/png;base64,${data.image}`;
            } else {
                graphImg.src = "https://via.placeholder.com/400x200?text=Graph+Not+Available";
            }
        })
        .catch(error => {
            console.error('Error fetching growth graph:', error);
            const graphImg = document.getElementById('growth-graph');
            graphImg.src = "https://via.placeholder.com/400x200?text=Error+Loading+Graph";
        });
}

// Fetch and display seasonal status
export function fetchSeasonalStatus() {
    fetchData(endpoints.seasonalStatus, 'seasonal-status-table-body', row => `
        <td>${row.plant_name}</td>
        <td>${row.start_date}</td>
        <td>${row.current_stage}</td>
    `);
}