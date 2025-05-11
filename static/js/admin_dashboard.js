// Initialize when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Tab switching functionality
    initTabSwitching();
    
    // Initialize plant selectors
    initPlantSelectors();
    
    // Get default plants for initial data loading
    const defaultSolarPlantId = document.getElementById('solar-plant-select').value;
    const defaultWindPlantId = document.getElementById('wind-plant-select').value;
    
    // Initialize initial charts with default plant data
    initDailyCharts();
    
    // Explicitly fetch data for the default selected plants
    fetchSolarDailyData(defaultSolarPlantId);
    fetchWindDailyData(defaultWindPlantId);
    
    // Set up date selector event listeners
    initDateSelectors();
    
    // Set up refresh button functionality
    initRefreshButton();
    
    // Initially fetch hourly data for default plants (but don't render until tab is clicked)
    fetchSolarHourlyData(document.getElementById('solar-date-select').value, defaultSolarPlantId);
    fetchWindHourlyData(document.getElementById('wind-date-select').value, defaultWindPlantId);
    
    // Add console debug logging
    console.log('Admin dashboard initialized with default plants:', {
        solarPlant: defaultSolarPlantId,
        windPlant: defaultWindPlantId
    });
});

// Tab switching functionality
function initTabSwitching() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Get the tab id to show
            const tabId = this.getAttribute('data-tab');
            
            // Hide all tab contents and deactivate all tabs in this container
            const tabContainer = this.closest('.tab-container');
            tabContainer.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            
            // Find all tab contents that are siblings of this tab container
            const tabContents = tabContainer.parentElement.querySelectorAll('.tab-content');
            tabContents.forEach(content => content.classList.remove('active'));
            
            // Activate selected tab and content
            this.classList.add('active');
            document.getElementById(tabId).classList.add('active');
            
            // Re-render charts if needed
            if (tabId === 'solar-hourly') {
                fetchSolarHourlyData(document.getElementById('solar-date-select').value, document.getElementById('solar-plant-select').value);
            } else if (tabId === 'wind-hourly') {
                fetchWindHourlyData(document.getElementById('wind-date-select').value, document.getElementById('wind-plant-select').value);
            }
        });
    });
}

// Initialize plant selectors
function initPlantSelectors() {
    // Solar plant selector
    const solarPlantSelector = document.getElementById('solar-plant-select');
    if (solarPlantSelector) {
        solarPlantSelector.addEventListener('change', function() {
            const plantId = this.value;
            updateSolarData(plantId);
        });
    }
    
    // Wind plant selector
    const windPlantSelector = document.getElementById('wind-plant-select');
    if (windPlantSelector) {
        windPlantSelector.addEventListener('change', function() {
            const plantId = this.value;
            updateWindData(plantId);
        });
    }
}

// Update solar data based on selected plant
function updateSolarData(plantId) {
    // Update daily chart
    fetchSolarDailyData(plantId);
    
    // Update hourly chart if that tab is active
    if (!document.getElementById('solar-hourly').classList.contains('hidden')) {
        fetchSolarHourlyData(document.getElementById('solar-date-select').value, plantId);
    }
}

// Update wind data based on selected plant
function updateWindData(plantId) {
    // Update daily chart
    fetchWindDailyData(plantId);
    
    // Update hourly chart if that tab is active
    if (!document.getElementById('wind-hourly').classList.contains('hidden')) {
        fetchWindHourlyData(document.getElementById('wind-date-select').value, plantId);
    }
}

// Initialize daily charts
function initDailyCharts() {
    // Get defaults for chart colors
    const solarColors = {
        primary: 'rgba(22, 163, 74, 1)',
        primaryLight: 'rgba(22, 163, 74, 0.7)',
        secondary: 'rgba(134, 239, 172, 1)',
        secondaryLight: 'rgba(134, 239, 172, 0.7)',
    };
    
    const windColors = {
        primary: 'rgba(59, 130, 246, 1)',
        primaryLight: 'rgba(59, 130, 246, 0.7)',
        secondary: 'rgba(147, 197, 253, 1)',
        secondaryLight: 'rgba(147, 197, 253, 0.7)',
    };
    
    // Initialize solar daily chart
    initSolarDailyChart(solarColors);
    
    // Initialize wind daily chart
    initWindDailyChart(windColors);
}

// Initialize solar daily chart
function initSolarDailyChart(colors) {
    const solarDailyCtx = document.getElementById('solarDailyChart').getContext('2d');
    
    // Get data from data attributes
    const chartContainer = document.getElementById('solar-daily-chart-container');
    
    try {
        console.log('Initializing solar daily chart with container data:', chartContainer.dataset);
        let labels, predictions, actuals;
        
        // Try to parse data or provide fallback
        try {
            labels = JSON.parse(chartContainer.dataset.labels || '[]');
            predictions = JSON.parse(chartContainer.dataset.predictions || '[]');
            actuals = JSON.parse(chartContainer.dataset.actuals || '[]');
        } catch (e) {
            console.error('Error parsing solar chart data:', e);
            // Default fallback data
            labels = ['No Data'];
            predictions = [0];
            actuals = [0];
        }
        
        // Check if we have empty data and provide fallback
        if (labels.length === 0) {
            console.warn('No solar chart data available, using fallback');
            labels = ['No Data'];
            predictions = [0];
            actuals = [0];
        }
        
        console.log('Parsed chart data:', { labels, predictions, actuals });
        
        window.solarDailyChart = new Chart(solarDailyCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Predicted Generation (kWh)',
                        data: predictions,
                        backgroundColor: colors.primaryLight,
                        borderColor: colors.primary,
                        borderWidth: 1
                    },
                    {
                        label: 'Actual Generation (kWh)',
                        data: actuals,
                        backgroundColor: colors.secondaryLight,
                        borderColor: colors.secondary,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Generation (kWh)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Solar Daily Generation Forecast',
                        font: {
                            size: 16
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing solar daily chart:', error);
        document.getElementById('solarDailyChart').innerHTML = 'Error loading chart';
    }
}

// Initialize wind daily chart
function initWindDailyChart(colors) {
    const windDailyCtx = document.getElementById('windDailyChart').getContext('2d');
    
    // Get data from data attributes
    const chartContainer = document.getElementById('wind-daily-chart-container');
    
    try {
        console.log('Initializing wind daily chart with container data:', chartContainer.dataset);
        let labels, predictions, actuals;
        
        // Try to parse data or provide fallback
        try {
            labels = JSON.parse(chartContainer.dataset.labels || '[]');
            predictions = JSON.parse(chartContainer.dataset.predictions || '[]');
            actuals = JSON.parse(chartContainer.dataset.actuals || '[]');
        } catch (e) {
            console.error('Error parsing wind chart data:', e);
            // Default fallback data
            labels = ['No Data'];
            predictions = [0];
            actuals = [0];
        }
        
        // Check if we have empty data and provide fallback
        if (labels.length === 0) {
            console.warn('No wind chart data available, using fallback');
            labels = ['No Data'];
            predictions = [0];
            actuals = [0];
        }
        
        console.log('Parsed chart data:', { labels, predictions, actuals });
        
        window.windDailyChart = new Chart(windDailyCtx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Predicted Generation (kWh)',
                        data: predictions,
                        backgroundColor: colors.primaryLight,
                        borderColor: colors.primary,
                        borderWidth: 1
                    },
                    {
                        label: 'Actual Generation (kWh)',
                        data: actuals,
                        backgroundColor: colors.secondaryLight,
                        borderColor: colors.secondary,
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Generation (kWh)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                },
                plugins: {
                    title: {
                        display: true,
                        text: 'Wind Daily Generation Forecast',
                        font: {
                            size: 16
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing wind daily chart:', error);
        document.getElementById('windDailyChart').innerHTML = 'Error loading chart';
    }
}

// Initialize date selectors
function initDateSelectors() {
    document.getElementById('solar-date-select').addEventListener('change', function() {
        const plantId = document.getElementById('solar-plant-select').value;
        fetchSolarHourlyData(this.value, plantId);
    });
    
    document.getElementById('wind-date-select').addEventListener('change', function() {
        const plantId = document.getElementById('wind-plant-select').value;
        fetchWindHourlyData(this.value, plantId);
    });
}

// Function to fetch solar daily data
function fetchSolarDailyData(plantId) {
    console.log('Fetching solar daily data for plant:', plantId);
    
    fetch(`/api/solar_chart_data?plant_id=${plantId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received solar daily data:', data);
            updateSolarDailyChart(data);
        })
        .catch(error => {
            console.error('Error fetching solar daily data:', error);
        });
}

// Function to fetch wind daily data
function fetchWindDailyData(plantId) {
    console.log('Fetching wind daily data for plant:', plantId);
    
    fetch(`/api/wind_chart_data?plant_id=${plantId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received wind daily data:', data);
            updateWindDailyChart(data);
        })
        .catch(error => {
            console.error('Error fetching wind daily data:', error);
        });
}

// Function to update solar daily chart
function updateSolarDailyChart(data) {
    console.log('Updating solar daily chart with data:', data);
    
    if (window.solarDailyChart) {
        window.solarDailyChart.data.labels = data.dates;
        window.solarDailyChart.data.datasets[0].data = data.predictions;
        window.solarDailyChart.data.datasets[1].data = data.actuals;
        window.solarDailyChart.update();
    } else {
        console.error('Solar daily chart not initialized');
    }
}

// Function to update wind daily chart
function updateWindDailyChart(data) {
    console.log('Updating wind daily chart with data:', data);
    
    if (window.windDailyChart) {
        window.windDailyChart.data.labels = data.dates;
        window.windDailyChart.data.datasets[0].data = data.predictions;
        window.windDailyChart.data.datasets[1].data = data.actuals;
        window.windDailyChart.update();
    } else {
        console.error('Wind daily chart not initialized');
    }
}

// Function to fetch and render solar hourly data
function fetchSolarHourlyData(date, plantId) {
    console.log('Fetching solar hourly data:', { date, plantId });
    
    // Clear any previous error messages and ensure clean container
    const chartContainer = document.getElementById('solarHourlyChart').parentNode;
    if (chartContainer) {
        // First, try to destroy any existing chart to prevent memory leaks
        if (window.solarHourlyChart && typeof window.solarHourlyChart.destroy === 'function') {
            try {
                window.solarHourlyChart.destroy();
                console.log('Destroyed existing solar hourly chart before fetching new data');
            } catch (e) {
                console.warn('Error destroying existing solar chart:', e);
                window.solarHourlyChart = null;
            }
        }
        
        // Create fresh canvas
        chartContainer.innerHTML = `
            <canvas id="solarHourlyChart"></canvas>
            <div class="text-center py-4 text-gray-500">
                <div class="animate-spin inline-block w-6 h-6 border-2 border-gray-300 border-t-gray-600 rounded-full mb-2"></div>
                <p>Loading hourly data...</p>
            </div>
        `;
    }
    
    fetch(`/api/admin_hourly_data?type=solar&date=${date}&plant_id=${plantId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received solar hourly data:', data);
            
            // Verify data format first
            if (!data.success) {
                throw new Error(data.message || 'API returned unsuccessful response');
            }
            
            if (!data.hours || !data.total_predicted || !data.total_actual) {
                throw new Error('Missing required data fields in API response');
            }
            
            // Get a fresh reference to the canvas container
            const freshContainer = document.getElementById('solarHourlyChart').parentNode;
            
            // Ensure the loading indicator is removed
            if (freshContainer) {
                // Clear loading indicator, but keep the canvas
                const canvas = document.getElementById('solarHourlyChart');
                freshContainer.innerHTML = '';
                
                // Create a new canvas element with the same ID
                const newCanvas = document.createElement('canvas');
                newCanvas.id = 'solarHourlyChart';
                freshContainer.appendChild(newCanvas);
                
                // Render chart with delay to ensure DOM is updated
                setTimeout(() => renderSolarHourlyChart(data), 0);
            }
        })
        .catch(error => {
            console.error('Error fetching solar hourly data:', error);
            // Display detailed error message in the chart area
            showChartError('solarHourlyChart', 'Error loading data', error.message, 'error');
        });
}

// Function to fetch and render wind hourly data
function fetchWindHourlyData(date, plantId) {
    console.log('Fetching wind hourly data:', { date, plantId });
    
    // Clear any previous error messages and ensure clean container
    const chartContainer = document.getElementById('windHourlyChart').parentNode;
    if (chartContainer) {
        // First, try to destroy any existing chart to prevent memory leaks
        if (window.windHourlyChart && typeof window.windHourlyChart.destroy === 'function') {
            try {
                window.windHourlyChart.destroy();
                console.log('Destroyed existing wind hourly chart before fetching new data');
            } catch (e) {
                console.warn('Error destroying existing wind chart:', e);
                window.windHourlyChart = null;
            }
        }
        
        // Create fresh canvas
        chartContainer.innerHTML = `
            <canvas id="windHourlyChart"></canvas>
            <div class="text-center py-4 text-gray-500">
                <div class="animate-spin inline-block w-6 h-6 border-2 border-gray-300 border-t-gray-600 rounded-full mb-2"></div>
                <p>Loading hourly data...</p>
            </div>
        `;
    }
    
    fetch(`/api/admin_hourly_data?type=wind&date=${date}&plant_id=${plantId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Received wind hourly data:', data);
            
            // Verify data format first
            if (!data.success) {
                throw new Error(data.message || 'API returned unsuccessful response');
            }
            
            if (!data.hours || !data.total_predicted || !data.total_actual) {
                throw new Error('Missing required data fields in API response');
            }
            
            // Get a fresh reference to the canvas container
            const freshContainer = document.getElementById('windHourlyChart').parentNode;
            
            // Ensure the loading indicator is removed
            if (freshContainer) {
                // Clear loading indicator, but keep the canvas
                const canvas = document.getElementById('windHourlyChart');
                freshContainer.innerHTML = '';
                
                // Create a new canvas element with the same ID
                const newCanvas = document.createElement('canvas');
                newCanvas.id = 'windHourlyChart';
                freshContainer.appendChild(newCanvas);
                
                // Render chart with delay to ensure DOM is updated
                setTimeout(() => renderWindHourlyChart(data), 0);
            }
        })
        .catch(error => {
            console.error('Error fetching wind hourly data:', error);
            // Display detailed error message in the chart area
            showChartError('windHourlyChart', 'Error loading data', error.message, 'error');
        });
}

// Function to render solar hourly chart
function renderSolarHourlyChart(data) {
    try {
        console.log('Rendering solar hourly chart with data:', data);
        
        const solarHourlyCtx = document.getElementById('solarHourlyChart');
        if (!solarHourlyCtx) {
            console.error('Cannot find solar hourly chart canvas element');
            return;
        }
        
        // Get context
        const ctx = solarHourlyCtx.getContext('2d');
        if (!ctx) {
            console.error('Cannot get 2d context for solar hourly chart');
            return;
        }
        
        // Verify we have the necessary data
        if (!data.hours || !data.total_predicted || !data.total_actual) {
            console.error('Missing required data for solar hourly chart:', data);
            showChartError('solarHourlyChart', 'Invalid Data Format', 'The chart data is incomplete or in an unexpected format.', 'error');
            return;
        }
        
        // Properly destroy existing chart if it exists
        if (window.solarHourlyChart && typeof window.solarHourlyChart.destroy === 'function') {
            window.solarHourlyChart.destroy();
            console.log('Existing solar hourly chart destroyed');
        } else if (window.solarHourlyChart) {
            console.warn('Existing solar hourly chart found but destroy method is not available');
            window.solarHourlyChart = null;
        }
        
        // Create datasets
        const datasets = [
            {
                label: 'Total Predicted',
                data: data.total_predicted,
                borderColor: 'rgba(22, 163, 74, 1)',
                backgroundColor: 'rgba(22, 163, 74, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.3
            },
            {
                label: 'Total Actual',
                data: data.total_actual,
                borderColor: 'rgba(134, 239, 172, 1)',
                backgroundColor: 'rgba(134, 239, 172, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.3
            }
        ];
        
        // Add individual plant data if available and there are multiple plants
        if (data.plant_names && data.plant_names.length > 1) {
            // Add a dataset for each plant's predicted generation
            data.plant_names.forEach((plantName, index) => {
                if (data.plant_data && data.plant_data[plantName]) {
                    datasets.push({
                        label: `${plantName} Predicted`,
                        data: data.plant_data[plantName].predicted,
                        borderColor: getRandomColor(index),
                        borderWidth: 1,
                        borderDash: [5, 5],
                        fill: false,
                        hidden: true  // Hidden by default to avoid clutter
                    });
                }
            });
        }
        
        // Create the chart
        window.solarHourlyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.hours,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Solar Hourly Generation - ${data.date}`,
                        font: {
                            size: 16
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Generation (kWh)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Hour'
                        }
                    }
                }
            }
        });
        
        console.log('Solar hourly chart created successfully');
    } catch (error) {
        console.error('Error rendering solar hourly chart:', error);
        showChartError('solarHourlyChart', 'Chart Error', error.message, 'error');
    }
}

// Function to render wind hourly chart
function renderWindHourlyChart(data) {
    try {
        console.log('Rendering wind hourly chart with data:', data);
        
        const windHourlyCtx = document.getElementById('windHourlyChart');
        if (!windHourlyCtx) {
            console.error('Cannot find wind hourly chart canvas element');
            return;
        }
        
        // Get context
        const ctx = windHourlyCtx.getContext('2d');
        if (!ctx) {
            console.error('Cannot get 2d context for wind hourly chart');
            return;
        }
        
        // Verify we have the necessary data
        if (!data.hours || !data.total_predicted || !data.total_actual) {
            console.error('Missing required data for wind hourly chart:', data);
            showChartError('windHourlyChart', 'Invalid Data Format', 'The chart data is incomplete or in an unexpected format.', 'error');
            return;
        }
        
        // Properly destroy existing chart if it exists
        if (window.windHourlyChart && typeof window.windHourlyChart.destroy === 'function') {
            window.windHourlyChart.destroy();
            console.log('Existing wind hourly chart destroyed');
        } else if (window.windHourlyChart) {
            console.warn('Existing wind hourly chart found but destroy method is not available');
            window.windHourlyChart = null;
        }
        
        // Create datasets
        const datasets = [
            {
                label: 'Total Predicted',
                data: data.total_predicted,
                borderColor: 'rgba(59, 130, 246, 1)',
                backgroundColor: 'rgba(59, 130, 246, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.3
            },
            {
                label: 'Total Actual',
                data: data.total_actual,
                borderColor: 'rgba(147, 197, 253, 1)',
                backgroundColor: 'rgba(147, 197, 253, 0.1)',
                borderWidth: 2,
                fill: false,
                tension: 0.3
            }
        ];
        
        // Add individual plant data if available and there are multiple plants
        if (data.plant_names && data.plant_names.length > 1) {
            // Add a dataset for each plant's predicted generation
            data.plant_names.forEach((plantName, index) => {
                if (data.plant_data && data.plant_data[plantName]) {
                    datasets.push({
                        label: `${plantName} Predicted`,
                        data: data.plant_data[plantName].predicted,
                        borderColor: getRandomColor(index + 10), // Offset to get different colors than solar
                        borderWidth: 1,
                        borderDash: [5, 5],
                        fill: false,
                        hidden: true  // Hidden by default to avoid clutter
                    });
                }
            });
        }
        
        // Create the chart
        window.windHourlyChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.hours,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: `Wind Hourly Generation - ${data.date}`,
                        font: {
                            size: 16
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Generation (kWh)'
                        }
                    },
                    x: {
                        title: {
                            display: true,
                            text: 'Hour'
                        }
                    }
                }
            }
        });
        
        console.log('Wind hourly chart created successfully');
    } catch (error) {
        console.error('Error rendering wind hourly chart:', error);
        showChartError('windHourlyChart', 'Chart Error', error.message, 'error');
    }
}

// Initialize refresh button
function initRefreshButton() {
    const refreshBtn = document.getElementById('refreshData');
    if (refreshBtn) {
        refreshBtn.addEventListener('click', function() {
            // Show loading state
            this.disabled = true;
            this.innerHTML = '<svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Refreshing...';
            
            // Call API to refresh forecasts
            fetch('/api/update_forecasts')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    console.log('Forecast update successful, reloading page');
                    // Reload the page regardless of the response to get fresh data
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Error refreshing forecasts:', error);
                    this.disabled = false;
                    this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" /></svg> Refresh Data';
                    alert('Failed to refresh forecasts. Please try again.');
                });
        });
    }
    
    // Solar forecast refresh
    const solarRefreshBtn = document.getElementById('refreshSolarData');
    if (solarRefreshBtn) {
        solarRefreshBtn.addEventListener('click', function() {
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Refreshing...';
            
            fetch('/api/update_solar_forecasts')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    console.log('Solar forecast update successful, reloading page');
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Error refreshing solar forecasts:', error);
                    this.disabled = false;
                    this.innerHTML = originalText;
                    alert('Failed to refresh solar forecasts. Please try again.');
                });
        });
    }
    
    // Wind forecast refresh
    const windRefreshBtn = document.getElementById('refreshWindData');
    if (windRefreshBtn) {
        windRefreshBtn.addEventListener('click', function() {
            this.disabled = true;
            const originalText = this.innerHTML;
            this.innerHTML = '<svg class="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Refreshing...';
            
            fetch('/api/update_wind_forecasts')
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    console.log('Wind forecast update successful, reloading page');
                    window.location.reload();
                })
                .catch(error => {
                    console.error('Error refreshing wind forecasts:', error);
                    this.disabled = false;
                    this.innerHTML = originalText;
                    alert('Failed to refresh wind forecasts. Please try again.');
                });
        });
    }
}

// Helper function to generate random colors
function getRandomColor(index) {
    const colors = [
        'rgba(255, 99, 132, 1)',
        'rgba(54, 162, 235, 1)',
        'rgba(255, 206, 86, 1)',
        'rgba(75, 192, 192, 1)',
        'rgba(153, 102, 255, 1)',
        'rgba(255, 159, 64, 1)',
        'rgba(199, 199, 199, 1)',
        'rgba(83, 102, 255, 1)',
        'rgba(40, 159, 64, 1)',
        'rgba(210, 199, 199, 1)',
        'rgba(78, 52, 199, 1)',
        'rgba(225, 29, 72, 1)',
        'rgba(79, 70, 229, 1)',
        'rgba(16, 185, 129, 1)',
        'rgba(245, 158, 11, 1)',
    ];
    
    // Use modulo to cycle through colors if index is larger than array
    return colors[index % colors.length];
}

// Helper function to show chart errors
function showChartError(chartId, title, message, type = 'warning') {
    console.log(`Showing chart error for ${chartId}: ${title} - ${message}`);
    
    try {
        const chartCanvas = document.getElementById(chartId);
        if (!chartCanvas || !chartCanvas.parentNode) {
            console.error(`Cannot find chart canvas or parent for ID: ${chartId}`);
            return;
        }
        
        const containerDiv = chartCanvas.parentNode;
        const iconColor = type === 'error' ? 'text-red-500' : 'text-gray-400';
        const iconPath = type === 'error' 
            ? 'M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'  // Error icon
            : 'M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z';  // Info icon
            
        // Generate retry function based on chart type
        const retryFunctionName = chartId === 'windHourlyChart' ? 'retryWindHourlyChart' : 'retrySolarHourlyChart';
        
        // Create the error UI with retry button
        containerDiv.innerHTML = `
            <div style="display: flex; height: 200px; align-items: center; justify-content: center; color: #666; flex-direction: column;">
                <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mb-4 ${iconColor}" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${iconPath}" />
                </svg>
                <p class="font-medium">${title}</p>
                <p class="text-sm text-gray-500">${message}</p>
                <button onclick="${retryFunctionName}()" class="mt-4 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded text-sm">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 inline-block mr-1" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
                    </svg>
                    Retry
                </button>
            </div>
        `;
        
        // Add the retry functions to window scope so they can be called from the onclick attribute
        window.retryWindHourlyChart = function() {
            const date = document.getElementById('wind-date-select').value;
            const plantId = document.getElementById('wind-plant-select').value;
            fetchWindHourlyData(date, plantId);
        };
        
        window.retrySolarHourlyChart = function() {
            const date = document.getElementById('solar-date-select').value;
            const plantId = document.getElementById('solar-plant-select').value;
            fetchSolarHourlyData(date, plantId);
        };
    } catch (error) {
        console.error('Error displaying chart error message:', error);
    }
}
