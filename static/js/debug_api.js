// Debug script for API testing
document.addEventListener('DOMContentLoaded', function() {
    // Get current date in YYYY-MM-DD format
    const today = new Date().toISOString().split('T')[0];
    
    // Get plant ID from the dashboard if available
    const plantId = document.querySelector('.dashboard-container')?.dataset?.plantId || '2';
    
    console.log(`DEBUG: Today's date = ${today}`);
    console.log(`DEBUG: Plant ID = ${plantId}`);
    
    // Test hourly solar data endpoint
    console.log(`DEBUG: Testing hourly solar data endpoint...`);
    fetch(`/api/hourly_solar_data?date=${today}&plant_id=${plantId}`)
        .then(response => {
            console.log(`DEBUG: Response status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('DEBUG: Hourly solar data response:', data);
            if (data.success) {
                console.log(`DEBUG: Received ${data.hours.length} hours of data`);
            }
        })
        .catch(error => {
            console.error('DEBUG ERROR: Fetching hourly solar data failed:', error);
        });
    
    // Test solar chart data endpoint
    console.log(`DEBUG: Testing solar chart data endpoint...`);
    fetch(`/api/solar_chart_data?plant_id=${plantId}`)
        .then(response => {
            console.log(`DEBUG: Response status: ${response.status}`);
            return response.json();
        })
        .then(data => {
            console.log('DEBUG: Solar chart data response:', data);
        })
        .catch(error => {
            console.error('DEBUG ERROR: Fetching solar chart data failed:', error);
        });
}); 