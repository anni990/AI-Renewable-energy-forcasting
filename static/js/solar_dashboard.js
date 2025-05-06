document.addEventListener('DOMContentLoaded', function() {
    // Get plant ID from a data attribute
    const plantId = document.querySelector('.dashboard-container')?.dataset?.plantId || '';
    
    // Calculate and update "vs Yesterday" percentage
    function updateVsYesterday() {
        fetch(`/api/solar_chart_data?plant_id=${plantId}`)
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
        fetch(`/api/solar_chart_data?plant_id=${plantId}`)
            .then(response => response.json())
            .then(data => {
                // Use the most recent prediction value (first in the array)
                if (data.predictions && data.predictions.length > 0) {
                    const latestGeneration = data.predictions[0];
                    generationElement.textContent = `${latestGeneration.toFixed(1)} kWh`;
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
        fetch(`/api/hourly_solar_data?date=${today}&plant_id=${plantId}`)
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
                        borderColor: '#7f7fd5', // Updated to new primary color
                        backgroundColor: 'rgba(127, 127, 213, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Actual Generation (kWh)',
                        data: hourlyActuals,
                        borderColor: '#91eae4', // Updated to new accent color
                        backgroundColor: 'rgba(145, 234, 228, 0.1)',
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
            fetch(`/api/solar_chart_data?plant_id=${plantId}`)
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
                        option.textContent = i === 0 ? `${dateStr} (Today)` : 
                                             i === 1 ? `${dateStr} (Tomorrow)` : dateStr;
                        dateSelector.appendChild(option);
                    }
                    
                    // Fetch data for today
                    fetchHourlyData(today.toISOString().split('T')[0]);
                });
            
            // Add event listener for date change
            dateSelector.addEventListener('change', function() {
                const selectedDate = this.value;
                fetchHourlyData(selectedDate);
            });
            
            // Function to fetch hourly data for selected date
            function fetchHourlyData(selectedDate) {
                // Show loading state on chart
                if (hourlyChart) {
                    hourlyChart.data.datasets[0].data = [];
                    hourlyChart.data.datasets[1].data = [];
                    hourlyChart.update();
                }
                
                // Make AJAX request to get hourly data for selected date
                fetch(`/api/hourly_solar_data?date=${selectedDate}&plant_id=${plantId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            // Update chart data
                            hourlyChart.data.labels = data.hours;
                            hourlyChart.data.datasets[0].data = data.predictions;
                            hourlyChart.data.datasets[1].data = data.actuals;
                            
                            // For future dates, actual generation will be empty, so update the label
                            const today = new Date();
                            const selectedDateObj = new Date(selectedDate);
                            if (selectedDateObj > today) {
                                // This is a future date
                                hourlyChart.data.datasets[1].label = 'Estimated Actual Generation (kWh)';
                                hourlyChart.data.datasets[1].borderDash = [5, 5]; // Add dashed line for future actuals
                                
                                // Add a notice above the chart
                                const chartContainer = hourlyChartCanvas.parentElement.parentElement;
                                let noticeElement = chartContainer.querySelector('.future-notice');
                                
                                if (!noticeElement) {
                                    noticeElement = document.createElement('div');
                                    noticeElement.className = 'future-notice bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4 rounded-r';
                                    chartContainer.insertBefore(noticeElement, chartContainer.firstChild);
                                }
                                
                                // Calculate days in future
                                const daysInFuture = Math.floor((selectedDateObj - today) / (1000 * 60 * 60 * 24)) + 1;
                                noticeElement.innerHTML = `
                                    <div class="flex">
                                        <div class="flex-shrink-0">
                                            <svg class="h-5 w-5 text-yellow-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                                <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clip-rule="evenodd" />
                                            </svg>
                                        </div>
                                        <div class="ml-3">
                                            <p class="text-sm text-yellow-700">
                                                Showing solar generation forecast for <strong>${daysInFuture} day${daysInFuture > 1 ? 's' : ''} in the future</strong>. Actual values will be recorded once this date arrives.
                                            </p>
                                        </div>
                                    </div>
                                `;
                            } else {
                                // Past or current date
                                hourlyChart.data.datasets[1].label = 'Actual Generation (kWh)';
                                hourlyChart.data.datasets[1].borderDash = []; // Remove dashed line
                                
                                // Remove notice if it exists
                                const chartContainer = hourlyChartCanvas.parentElement.parentElement;
                                const noticeElement = chartContainer.querySelector('.future-notice');
                                if (noticeElement) {
                                    noticeElement.remove();
                                }
                            }
                            
                            hourlyChart.update();
                        } else {
                            console.error('Error fetching hourly data:', data.message);
                            // Show empty chart with message
                            const ctx = hourlyChartCanvas.getContext('2d');
                            ctx.font = '16px Arial';
                            ctx.fillStyle = '#666';
                            ctx.textAlign = 'center';
                            ctx.fillText('No data available for selected date', hourlyChartCanvas.width/2, hourlyChartCanvas.height/2);
                            
                            // Remove notice if it exists
                            const chartContainer = hourlyChartCanvas.parentElement.parentElement;
                            const noticeElement = chartContainer.querySelector('.future-notice');
                            if (noticeElement) {
                                noticeElement.remove();
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        // Handle error state
                        if (hourlyChart) {
                            hourlyChart.data.datasets[0].data = [];
                            hourlyChart.data.datasets[1].data = [];
                            hourlyChart.update();
                        }
                        
                        // Remove notice if it exists
                        const chartContainer = hourlyChartCanvas.parentElement.parentElement;
                        const noticeElement = chartContainer.querySelector('.future-notice');
                        if (noticeElement) {
                            noticeElement.remove();
                        }
                    });
            }
        }
    }

    // Initialize daily chart
    const dailyChartCanvas = document.getElementById('dailyChart');
    if (dailyChartCanvas) {
        // Check if data arrays are empty
        if (!dailyLabels.length || !dailyPredictions.length) {
            // Fetch data from API if template data is empty
            fetch(`/api/solar_chart_data?plant_id=${plantId}`)
                .then(response => response.json())
                .then(data => {
                    // Update arrays with fetched data
                    dailyLabels = data.dates || [];
                    dailyPredictions = data.predictions || [];
                    dailyActuals = data.actuals || [];
                    dailyThresholds = new Array(dailyLabels.length).fill(data.threshold || 0);
                    
                    // Initialize chart with fetched data
                    initializeDailyChart();
                })
                .catch(error => {
                    console.error('Error fetching chart data:', error);
                    // Initialize with empty data as fallback
                    initializeDailyChart();
                });
        } else {
            // Initialize with existing data
            initializeDailyChart();
        }
        
        function initializeDailyChart() {
            const dailyChart = new Chart(dailyChartCanvas, {
                type: 'bar',
                data: {
                    labels: dailyLabels,
                    datasets: [
                        {
                            label: 'Predicted Generation (kWh)',
                            data: dailyPredictions,
                            backgroundColor: 'rgba(127, 127, 213, 0.7)',
                            borderColor: 'rgba(127, 127, 213, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Actual Generation (kWh)',
                            data: dailyActuals,
                            backgroundColor: 'rgba(145, 234, 228, 0.7)',
                            borderColor: 'rgba(145, 234, 228, 1)',
                            borderWidth: 1
                        },
                        {
                            label: 'Threshold Value',
                            data: dailyThresholds,
                            type: 'line',
                            borderColor: 'rgba(255, 99, 132, 1)',
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
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            mode: 'index',
                            intersect: false,
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
    
    // Initialize metrics chart (replacing efficiency pie chart)
    const metricsChartCanvas = document.getElementById('metricsChart');
    if (metricsChartCanvas) {
        fetch(`/api/solar_chart_data?plant_id=${plantId}`)
            .then(response => response.json())
            .then(data => {
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
                                'rgba(127, 127, 213, 0.7)',  // Solar primary
                                'rgba(134, 168, 231, 0.7)',  // Solar secondary
                                'rgba(255, 99, 132, 0.7)'    // Threshold red
                            ],
                            borderColor: [
                                'rgba(127, 127, 213, 1)',
                                'rgba(134, 168, 231, 1)',
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

    // Setup refresh data button
    const refreshButton = document.getElementById('refreshData');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            // Add loading state
            this.disabled = true;
            this.innerHTML = `
                <svg class="animate-spin h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Refreshing...
            `;
            
            // Call the API to refresh data
            fetch(`/api/refresh-solar-data`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Reload the page to show fresh data
                        window.location.reload();
                    } else {
                        alert('Error refreshing data: ' + data.message);
                        // Reset button state
                        this.disabled = false;
                        this.innerHTML = `
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                                <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
                            </svg>
                            Refresh Data
                        `;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Network error. Please try again.');
                    // Reset button state
                    this.disabled = false;
                    this.innerHTML = `
                        <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 mr-2" viewBox="0 0 20 20" fill="currentColor">
                            <path fill-rule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 010 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.276.61A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clip-rule="evenodd" />
                        </svg>
                        Refresh Data
                    `;
                });
        });
    }
    
    // Fetch weather data
    fetchWeatherData();
});

// Fetch weather data from API
function fetchWeatherData() {
    fetch('/api/weather-data')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Update weather condition display
                const weatherData = data.data;
                const condition = weatherData.condition || 'Unknown';
                const temperature = weatherData.temperature || 0;
                const windSpeed = weatherData.wind_speed || 0;
                const radiation = weatherData.radiation || 0;
                
                // Update weather condition display with icon
                document.getElementById('weather-condition').innerHTML = getWeatherIcon(condition) + ' ' + condition;
                
                // Update weather impact text
                let impactText = '';
                if (condition === 'Sunny' || condition === 'Clear') {
                    impactText = 'Optimal for solar generation';
                } else if (condition === 'Cloudy' || condition === 'Partly Cloudy') {
                    impactText = 'Reduced efficiency due to cloud cover';
                } else {
                    impactText = 'Suboptimal for solar generation';
                }
                
                document.getElementById('weather-impact').textContent = impactText;
                
                // Create the weather detail cards
                const weatherContainer = document.getElementById('weather-data');
                if (weatherContainer) {
                    weatherContainer.innerHTML = `
                        <div class="text-center p-4 bg-solar-light rounded-lg">
                            <div class="text-3xl text-solar-primary mb-2">${getWeatherIcon(condition)}</div>
                            <p class="font-medium text-gray-700">${condition}</p>
                            <p class="text-sm text-gray-600">${impactText}</p>
                        </div>
                        <div class="text-center p-4 bg-solar-light rounded-lg">
                            <div class="text-3xl text-solar-primary mb-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M9 5.25h6M9 19h6"/>
                                </svg>
                            </div>
                            <p class="font-medium text-gray-700">${temperature.toFixed(1)}°C</p>
                            <p class="text-sm text-gray-600">Temperature</p>
                        </div>
                        <div class="text-center p-4 bg-solar-light rounded-lg">
                            <div class="text-3xl text-solar-primary mb-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4"/>
                                </svg>
                            </div>
                            <p class="font-medium text-gray-700">${windSpeed.toFixed(1)} km/h</p>
                            <p class="text-sm text-gray-600">Wind Speed</p>
                        </div>
                        <div class="text-center p-4 bg-solar-light rounded-lg">
                            <div class="text-3xl text-solar-primary mb-2">
                                <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z"/>
                                </svg>
                            </div>
                            <p class="font-medium text-gray-700">${radiation.toFixed(1)} W/m²</p>
                            <p class="text-sm text-gray-600">Solar Radiation</p>
                        </div>
                    `;
                }
            } else {
                console.error('Error fetching weather data:', data.message);
                document.getElementById('weather-condition').textContent = 'Weather data unavailable';
                document.getElementById('weather-impact').textContent = 'Could not retrieve weather information';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            document.getElementById('weather-condition').textContent = 'Weather data unavailable';
            document.getElementById('weather-impact').textContent = 'Network error retrieving weather information';
        });
}

// Helper function to get weather icon
function getWeatherIcon(condition) {
    switch (condition.toLowerCase()) {
        case 'sunny':
        case 'clear':
            return `<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 inline-block text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>`;
        
        case 'cloudy':
        case 'partly cloudy':
        case 'mostly cloudy':
            return `<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 inline-block text-gray-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>`;
        
        case 'rainy':
        case 'rain':
            return `<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 inline-block text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
            </svg>`;
        
        default:
            return `<svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8 inline-block text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
            </svg>`;
    }
} 