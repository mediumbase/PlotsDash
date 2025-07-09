import { updateDateTime } from './utils.js';
import { startDataFetching } from './dataFetch.js';

// Update the time and date every second
setInterval(updateDateTime, 1000);
updateDateTime(); // Initial call

// Start periodic data fetching
startDataFetching();