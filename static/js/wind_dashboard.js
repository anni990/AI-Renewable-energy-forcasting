document.addEventListener('DOMContentLoaded', function() {
    // Get plant ID from a data attribute
    const plantId = document.querySelector('.dashboard-container')?.dataset?.plantId || '';
    
    // Calculate and update "vs Yesterday" percentage
    function updateVsYesterday() {
        fetch(`/api/wind_chart_data?plant_id=${plantId}`)
            .then(response => response.json())
            .then(data => {
                if (data.predictions && data.predictions.length >= 2) {
                    const todayGen = data.predictions[0];
                    const yesterdayGen = data.predictions[1];
                    
                    if (yesterdayGen > 0) {
                        const percentChange = ((todayGen - yesterdayGen) / yesterdayGen * 100).toFixed(1);
                        const vsYesterdayElement = document.getElementById('vsYesterday');
                        
                        if (vsYesterdayElement) {
                            // Determine icon and color based on whether it's positive or negative
                            let icon, cssClass;
                            if (percentChange > 0) {
                                icon = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12 7a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0V8.414l-4.293 4.293a1 1 0 01-1.414 0L8 10.414l-4.293 4.293a1 1 0 01-1.414-1.414l5-5a1 1 0 011.414 0L11 10.586 14.586 7H12z" clip-rule="evenodd" /></svg>';
                                cssClass = 'text-green-500';
                            } else {
                                icon = '<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M12 13a1 1 0 100 2h5a1 1 0 001-1V9a1 1 0 10-2 0v2.586l-4.293-4.293a1 1 0 00-1.414 0L8 9.586 3.707 5.293a1 1 0 00-1.414 1.414l5 5a1 1 0 001.414 0L11 9.414 14.586 13H12z" clip-rule="evenodd" /></svg>';
                                cssClass = 'text-red-500';
                            }
                            
                            vsYesterdayElement.className = `flex items-center text-sm ${cssClass}`;
                            vsYesterdayElement.innerHTML = `${icon} ${Math.abs(percentChange)}% vs Yesterday`;
                        }
                    } else {
                        document.getElementById('vsYesterday').textContent = 'No data for yesterday';
                    }
                } else {
                    document.getElementById('vsYesterday').textContent = 'Insufficient data';
                }
            })
            .catch(error => {
                console.error('Error fetching generation data:', error);
                document.getElementById('vsYesterday').textContent = 'Error calculating';
            });
    }
    
    // Call the function to update the comparison
    updateVsYesterday();
    
    // Update generation stats if API data is available but UI shows zero
    const generationElement = document.querySelector('.stat-card .text-3xl');
    if (generationElement && (generationElement.textContent.trim() === '0 kWh' || 
                              generationElement.textContent.trim() === '0.0 kWh')) {
        fetch(`/api/wind_chart_data?plant_id=${plantId}`)
            .then(response => response.json())
            .then(data => {
                // Use the most recent prediction value (first in the array)
                if (data.predictions && data.predictions.length > 0) {
                    const latestGeneration = data.predictions[0];
                    generationElement.textContent = `${latestGeneration.toFixed(1)} kWh`;
                    
                    // Update efficiency value if available
                    if (data.threshold) {
                        const efficiencyElement = document.querySelector('.stat-card:nth-child(2) .text-3xl');
                        if (efficiencyElement) {
                            const efficiencyPercentage = Math.round((latestGeneration / data.threshold) * 100);
                            efficiencyElement.textContent = `${efficiencyPercentage}%`;
                            
                            // Update efficiency status text
                            const statusElement = document.querySelector('.stat-card:nth-child(2) .flex .text-sm');
                            if (statusElement) {
                                if (efficiencyPercentage > 90) {
                                    statusElement.textContent = 'Excellent';
                                    statusElement.className = 'text-sm text-green-500';
                                } else if (efficiencyPercentage > 70) {
                                    statusElement.textContent = 'Good';
                                    statusElement.className = 'text-sm text-yellow-500';
                                } else {
                                    statusElement.textContent = 'Needs Attention';
                                    statusElement.className = 'text-sm text-red-500';
                                }
                            }
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching generation data:', error);
            });
    }
    
    // Update peak generation hour if needed
    function updatePeakHour() {
        // Get today's date in YYYY-MM-DD format
        const today = new Date().toISOString().split('T')[0];
        
        // Fetch hourly data for today
        fetch(`/api/hourly_wind_data?date=${today}&plant_id=${plantId}`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.predictions && data.hours) {
                    // Find the peak hour
                    let maxVal = 0;
                    let peakHour = 'N/A';
                    
                    for (let i = 0; i < data.predictions.length; i++) {
                        if (data.predictions[i] > maxVal) {
                            maxVal = data.predictions[i];
                            peakHour = data.hours[i];
                        }
                    }
                    
                    // Update the DOM elements
                    const peakHourElement = document.getElementById('peak-hour');
                    const peakOutputElement = document.getElementById('peak-output');
                    
                    if (peakHourElement && peakHour !== 'N/A') {
                        peakHourElement.textContent = peakHour;
                        peakOutputElement.textContent = `${maxVal.toFixed(2)} kWh peak output`;
                    }
                }
            })
            .catch(error => {
                console.error('Error fetching peak hour data:', error);
            });
    }
    
    // Call the function to update peak hour
    updatePeakHour();
    
    // Initialize hourly chart
    const hourlyChartCanvas = document.getElementById('hourlyChart');
    if (hourlyChartCanvas) {
        const hourlyChart = new Chart(hourlyChartCanvas, {
            type: 'line',
            data: {
                labels: hourlyLabels,
                datasets: [
                    {
                        label: 'Predicted Generation (kWh)',
                        data: hourlyPredictions,
                        borderColor: '#3b82f6', // Wind primary color
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Actual Generation (kWh)',
                        data: hourlyActuals,
                        borderColor: '#93c5fd', // Wind accent color
                        backgroundColor: 'rgba(147, 197, 253, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    tooltip: {
                        mode: 'index',
                        intersect: false
                    },
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Energy Generation (kWh)'
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
        
        // Handle date selector change
        const dateSelector = document.getElementById('dateSelector');
        if (dateSelector) {
            // Clear existing options
            dateSelector.innerHTML = '';
            
            // Fetch latest 6 dates from database
            fetch(`/api/wind_chart_data?plant_id=${plantId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.dates && data.dates.length > 0) {
                        // Get the most recent 6 dates
                        const dates = data.dates.slice(0, 6);
                        
                        // Add the dates to the selector
                        dates.forEach((dateStr, index) => {
                            const option = document.createElement('option');
                            option.value = dateStr;
                            
                            // Format the date display
                            const date = new Date(dateStr);
                            const today = new Date();
                            today.setHours(0, 0, 0, 0);
                            
                            const dateObj = new Date(dateStr);
                            dateObj.setHours(0, 0, 0, 0);
                            
                            const tomorrow = new Date(today);
                            tomorrow.setDate(tomorrow.getDate() + 1);
                            
                            const yesterday = new Date(today);
                            yesterday.setDate(yesterday.getDate() - 1);
                            
                            if (dateObj.getTime() === today.getTime()) {
                                option.textContent = `${dateStr} (Today)`;
                            } else if (dateObj.getTime() === tomorrow.getTime()) {
                                option.textContent = `${dateStr} (Tomorrow)`;
                            } else if (dateObj.getTime() === yesterday.getTime()) {
                                option.textContent = `${dateStr} (Yesterday)`;
                            } else {
                                option.textContent = dateStr;
                            }
                            
                            dateSelector.appendChild(option);
                        });
                        
                        // Fetch data for initial selection (most recent date)
                        fetchHourlyData(dates[0]);
                    } else {
                        // If no dates from API, use today + next 5 days
                        const today = new Date();
                        for (let i = 0; i < 6; i++) {
                            const date = new Date(today);
                            date.setDate(today.getDate() + i);
                            const dateStr = date.toISOString().split('T')[0]; // Format as YYYY-MM-DD
                            
                            const option = document.createElement('option');
                            option.value = dateStr;
                            
                            // Add "Today" or "Tomorrow" for better UX
                            if (i === 0) {
                                option.textContent = `${dateStr} (Today)`;
                            } else if (i === 1) {
                                option.textContent = `${dateStr} (Tomorrow)`;
                            } else {
                                option.textContent = dateStr;
                            }
                            dateSelector.appendChild(option);
                        }
                        
                        // Fetch data for today
                        fetchHourlyData(today.toISOString().split('T')[0]);
                    }
                })
                .catch(error => {
                    console.error('Error fetching dates:', error);
                    
                    // Fallback to today + next 5 days
                    const today = new Date();
                    for (let i = 0; i < 6; i++) {
                        const date = new Date(today);
                        date.setDate(today.getDate() + i);
                        const dateStr = date.toISOString().split('T')[0]; // Format as YYYY-MM-DD
                        
                        const option = document.createElement('option');
                        option.value = dateStr;
                        
                        // Add "Today" or "Tomorrow" for better UX
                        if (i === 0) {
                            option.textContent = `${dateStr} (Today)`;
                        } else if (i === 1) {
                            option.textContent = `${dateStr} (Tomorrow)`;
                        } else {
                            option.textContent = dateStr;
                        }
                        dateSelector.appendChild(option);
                    }
                    
                    // Fetch data for today
                    fetchHourlyData(today.toISOString().split('T')[0]);
                });
            
            // Add event listener for date selector change
            dateSelector.addEventListener('change', function() {
                const selectedDate = this.value;
                fetchHourlyData(selectedDate);
            });
            
            function fetchHourlyData(selectedDate) {
                fetch(`/api/hourly_wind_data?date=${selectedDate}&plant_id=${plantId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Update chart data
                            hourlyChart.data.labels = data.hours;
                            hourlyChart.data.datasets[0].data = data.predictions;
                            hourlyChart.data.datasets[1].data = data.actuals;
                            hourlyChart.update();
                        } else {
                            console.error('Error fetching hourly data:', data.message);
                        }
                    })
                    .catch(error => {
                        console.error('Error fetching hourly data:', error);
                    });
            }
        }
    }
    
    // Initialize daily chart
    function initializeDailyChart() {
        const dailyChartCanvas = document.getElementById('dailyChart');
        if (dailyChartCanvas) {
            const dailyChart = new Chart(dailyChartCanvas, {
                type: 'bar',
                data: {
                    labels: dailyLabels,
                    datasets: [
                        {
                            label: 'Predicted Generation (kWh)',
                            data: dailyPredictions,
                            backgroundColor: 'rgba(59, 130, 246, 0.7)', // Wind primary color
                            borderColor: '#3b82f6',
                            borderWidth: 1
                        },
                        {
                            label: 'Actual Generation (kWh)',
                            data: dailyActuals,
                            backgroundColor: 'rgba(147, 197, 253, 0.7)', // Wind accent color
                            borderColor: '#93c5fd',
                            borderWidth: 1
                        },
                        {
                            label: 'Threshold (kWh)',
                            data: dailyThresholds,
                            type: 'line',
                            borderColor: '#ef4444', // Red
                            borderWidth: 2,
                            borderDash: [5, 5],
                            fill: false,
                            pointRadius: 0
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        tooltip: {
                            mode: 'index',
                            intersect: false
                        },
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            title: {
                                display: true,
                                text: 'Energy Generation (kWh)'
                            }
                        },
                        x: {
                            title: {
                                display: true,
                                text: 'Date'
                            }
                        }
                    }
                }
            });
        }
    }
    
    // Initialize metrics chart (bar chart replacing doughnut chart)
    function initializeMetricsChart() {
        const metricsChartCanvas = document.getElementById('metricsChart');
        if (metricsChartCanvas) {
            const plantId = document.querySelector('.dashboard-container')?.dataset?.plantId || '';
            
            fetch(`/api/wind_chart_data?plant_id=${plantId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Get the most recent prediction data
                        const latestPrediction = data.predictions && data.predictions.length > 0 ? data.predictions[0] : 0;
                        const threshold = data.threshold || 0;
                        
                        // Calculate metrics
                        const avgPrediction = data.predictions && data.predictions.length > 0 
                            ? data.predictions.reduce((sum, val) => sum + val, 0) / data.predictions.length 
                            : 0;
                        
                        // Create the metrics chart
                        const metricsChart = new Chart(metricsChartCanvas, {
                            type: 'bar',
                            data: {
                                labels: ['Today', '7-Day Avg', 'Threshold'],
                                datasets: [{
                                    label: 'Generation (kWh)',
                                    data: [latestPrediction, avgPrediction, threshold],
                                    backgroundColor: [
                                        'rgba(59, 130, 246, 0.7)',  // Wind primary
                                        'rgba(96, 165, 250, 0.7)',  // Wind secondary
                                        'rgba(255, 99, 132, 0.7)'   // Threshold red
                                    ],
                                    borderColor: [
                                        'rgba(59, 130, 246, 1)',
                                        'rgba(96, 165, 250, 1)',
                                        'rgba(255, 99, 132, 1)'
                                    ],
                                    borderWidth: 1
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        display: false
                                    },
                                    tooltip: {
                                        callbacks: {
                                            label: function(context) {
                                                return `${context.dataset.label}: ${context.raw.toFixed(1)} kWh`;
                                            }
                                        }
                                    }
                                },
                                scales: {
                                    y: {
                                        beginAtZero: true,
                                        title: {
                                            display: true,
                                            text: 'Energy (kWh)'
                                        }
                                    }
                                }
                            }
                        });
                    }
                })
                .catch(error => {
                    console.error('Error fetching metrics data:', error);
                    // Show error message in the canvas
                    const ctx = metricsChartCanvas.getContext('2d');
                    ctx.font = '14px Arial';
                    ctx.fillStyle = '#666';
                    ctx.textAlign = 'center';
                    ctx.fillText('Error loading metrics data', metricsChartCanvas.width/2, metricsChartCanvas.height/2);
                });
        }
    }
    
    // Call the functions to initialize charts
    initializeDailyChart();
    initializeMetricsChart();
    
    // Add refresh data functionality
    const refreshButton = document.getElementById('refreshData');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<svg class="animate-spin -ml-1 mr-2 h-5 w-5 text-wind-primary" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Refreshing...';
            
            // Call API to refresh data
            fetch('/api/refresh-wind-data')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Reload the page to show updated data
                        window.location.reload();
                    } else {
                        alert('Error refreshing data: ' + data.message);
                        this.disabled = false;
                        this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" /></svg> Refresh Data';
                    }
                })
                .catch(error => {
                    console.error('Error refreshing data:', error);
                    alert('Network error when refreshing data');
                    this.disabled = false;
                    this.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor"><path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" /></svg> Refresh Data';
                });
        });
    }
    
    // Fetch and display weather data
    fetchWeatherData();
});

// Fetch current weather data
function fetchWeatherData() {
    const plantId = document.querySelector('.dashboard-container')?.dataset?.plantId || '';
    
    fetch(`/api/weather-data?plant_id=${plantId}`)
        .then(response => response.json())
        .then(response => {
            if (response.success && response.data) {
                // Access data from the nested data property
                const data = response.data;
                
                // Update weather condition card
                updateWindCondition(data);
                
                // Update weather data grid
                const weatherDataContainer = document.getElementById('weather-data');
                if (weatherDataContainer) {
                    // Clear existing content
                    weatherDataContainer.innerHTML = '';
                    
                    // Create wind-specific weather cards
                    const windSpeed = data.wind_speed !== undefined ? data.wind_speed : 'Data unavailable';
                    const windDirection = data.wind_direction !== undefined ? data.wind_direction : 'Data unavailable';
                    const temperature = data.temperature !== undefined ? data.temperature : 'Data unavailable';
                    const humidity = data.humidity !== undefined ? data.humidity : 'Data unavailable';
                    
                    // Add wind speed card
                    weatherDataContainer.innerHTML += `
                        <div class="text-center p-4 bg-wind-light rounded-lg">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto text-wind-primary" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M5.05 3.636a1 1 0 010 1.414 7 7 0 000 9.9 1 1 0 11-1.414 1.414 9 9 0 010-12.728 1 1 0 011.414 0zm9.9 0a1 1 0 011.414 0 9 9 0 010 12.728 1 1 0 11-1.414-1.414 7 7 0 000-9.9 1 1 0 010-1.414zM7.879 6.464a1 1 0 010 1.414 3 3 0 000 4.243 1 1 0 11-1.415 1.414 5 5 0 010-7.07 1 1 0 011.415 0zm4.242 0a1 1 0 011.415 0 5 5 0 010 7.072 1 1 0 01-1.415-1.415 3 3 0 000-4.242 1 1 0 010-1.415z" clip-rule="evenodd" />
                            </svg>
                            <h4 class="text-lg font-semibold mt-2">Wind Speed</h4>
                            <p class="text-2xl font-bold wind-text-primary">${typeof windSpeed === 'number' ? `${windSpeed} m/s` : windSpeed}</p>
                        </div>
                    `;
                    
                    // Add wind direction card
                    weatherDataContainer.innerHTML += `
                        <div class="text-center p-4 bg-wind-light rounded-lg">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto text-wind-primary" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M5.293 7.707a1 1 0 010-1.414l4-4a1 1 0 011.414 0l4 4a1 1 0 01-1.414 1.414L11 5.414V17a1 1 0 11-2 0V5.414L6.707 7.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
                            </svg>
                            <h4 class="text-lg font-semibold mt-2">Wind Direction</h4>
                            <p class="text-2xl font-bold wind-text-primary">${!isNaN(windDirection) ? windDirection + '°' : windDirection}</p>
                        </div>
                    `;
                    
                    // Add temperature card
                    weatherDataContainer.innerHTML += `
                        <div class="text-center p-4 bg-wind-light rounded-lg">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto text-wind-primary" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1.323l3.954 1.582 1.599-.8a1 1 0 01.894 1.79l-1.233.616 1.738 5.42a1 1 0 01-.285 1.05A3.989 3.989 0 0115 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.715-5.349L11 6.477V16h2a1 1 0 110 2H7a1 1 0 110-2h2V6.477L6.237 7.582l1.715 5.349a1 1 0 01-.285 1.05A3.989 3.989 0 015 15a3.989 3.989 0 01-2.667-1.019 1 1 0 01-.285-1.05l1.738-5.42-1.233-.617a1 1 0 01.894-1.788l1.599.799L9 4.323V3a1 1 0 011-1z" clip-rule="evenodd" />
                            </svg>
                            <h4 class="text-lg font-semibold mt-2">Temperature</h4>
                            <p class="text-2xl font-bold wind-text-primary">${typeof temperature === 'number' ? `${temperature}°C` : temperature}</p>
                        </div>
                    `;
                    
                    // Add humidity card
                    weatherDataContainer.innerHTML += `
                        <div class="text-center p-4 bg-wind-light rounded-lg">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto text-wind-primary" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M7 2a1 1 0 00-.707 1.707L7 4.414v3.758a1 1 0 01-.293.707l-4 4C.817 14.769 2.156 18 4.828 18h10.343c2.673 0 4.012-3.231 2.122-5.121l-4-4A1 1 0 0113 8.172V4.414l.707-.707A1 1 0 0013 2H7zm2 6.172V4h2v4.172a3 3 0 00.879 2.12l1.168 1.168a4 4 0 00-2.366.376l-.009-.01-3.6-3.6a3 3 0 00-.879-2.121L6.8 6.6l-.6-.6V4h1.172L7 4.414v3.758a1 1 0 01-.293.707l-4 4C.817 14.769 2.156 18 4.828 18h10.343c2.673 0 4.012-3.231 2.122-5.121l-4-4A1 1 0 0113 8.172V4.414l.707-.707A1 1 0 0013 2H7z" clip-rule="evenodd" />
                            </svg>
                            <h4 class="text-lg font-semibold mt-2">Humidity</h4>
                            <p class="text-2xl font-bold wind-text-primary">${typeof humidity === 'number' ? `${humidity}%` : humidity}</p>
                        </div>
                    `;
                }
            } else {
                console.error('Error fetching weather data:', response.message);
            }
        })
        .catch(error => {
            console.error('Error fetching weather data:', error);
        });
}

// Update wind condition based on wind speed
function updateWindCondition(weatherData) {
    const windConditionElement = document.getElementById('wind-condition');
    const windImpactElement = document.getElementById('wind-impact');
    
    if (windConditionElement && windImpactElement && weatherData) {
        const windSpeed = weatherData.wind_speed;
        
        // Check if wind speed data is available
        if (windSpeed === undefined || windSpeed === null) {
            windConditionElement.textContent = 'Unknown';
            windConditionElement.className = 'text-3xl font-bold mb-2 text-gray-500';
            windImpactElement.textContent = 'Weather data unavailable';
            return;
        }
        
        let condition, impact, color;
        
        // Determine wind condition based on wind speed
        if (windSpeed < 3.0) {
            condition = 'Low Wind';
            impact = 'Minimal power generation';
            color = 'text-red-500';
        } else if (windSpeed >= 3.0 && windSpeed < 10.0) {
            condition = 'Moderate Wind';
            impact = 'Good generation conditions';
            color = 'text-green-500';
        } else if (windSpeed >= 10.0 && windSpeed < 20.0) {
            condition = 'Strong Wind';
            impact = 'Optimal generation conditions';
            color = 'text-green-500';
        } else if (windSpeed >= 20.0 && windSpeed < 25.0) {
            condition = 'Very Strong Wind';
            impact = 'Near maximum generation';
            color = 'text-green-500';
        } else {
            condition = 'Extreme Wind';
            impact = 'Turbine cut-out may occur';
            color = 'text-red-500';
        }
        
        windConditionElement.textContent = condition;
        windConditionElement.className = `text-3xl font-bold mb-2 ${color}`;
        windImpactElement.textContent = impact;
    }
} 