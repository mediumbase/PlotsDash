import { endpoints } from './routing.js';
import { fetchData } from './utils.js';

// Fetch and display harvest scheduler
export function fetchHarvestScheduler() {
    fetchData(endpoints.harvestScheduler, 'harvest-scheduler-table-body', row => `
        <td>${row.plant_name}</td>
        <td>${row.predicted_harvest_date}</td>
    `);
}