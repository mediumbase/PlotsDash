// Function to update the time and date
export function updateDateTime() {
    const now = new Date();
    const datetimeElement = document.getElementById("datetime");
    datetimeElement.textContent = now.toLocaleString();
}

// Reusable function to fetch and display data in a table
export async function fetchData(url, tableId, rowTemplate) {
    const tableBody = document.getElementById(tableId);
    tableBody.innerHTML = `<tr><td colspan="4">Loading...</td></tr>`; // Show loading indicator

    try {
        const response = await fetch(url);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        const data = await response.json();
        tableBody.innerHTML = ''; // Clear loading indicator
        data.forEach(row => {
            const tr = document.createElement('tr');
            tr.innerHTML = rowTemplate(row);
            tableBody.appendChild(tr);
        });
    } catch (error) {
        console.error(`Error fetching data from ${url}:`, error);
        tableBody.innerHTML = `<tr><td colspan="4">Failed to load data. Please try again later.</td></tr>`;
    }
}