import { fetchSensorData } from './dataSensor.js';
import { fetchGrowthRateData, fetchGrowthGraph, fetchSeasonalStatus } from './dataGrowth.js';
import { fetchHarvestScheduler } from './dataHarvest.js';
import { updateDetectionData } from './dataDetection.js';

// Periodically fetch and update data
export function startDataFetching() {
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
}