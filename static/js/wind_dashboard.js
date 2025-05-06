document.addEventListener('DOMContentLoaded', function() {
    // Get plant ID from a data attribute
    const plantId = document.querySelector('.dashboard-container')?.dataset?.plantId || '';
    
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
                        borderColor: '#7f7fd5',
                        backgroundColor: 'rgba(127, 127, 213, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Actual Generation (kWh)',
                        data: hourlyActuals,
                        borderColor: '#91eae4',
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
            
            // Add future dates (today + next 5 days)
            const today = new Date();
            for (let i = 0; i < 6; i++) { // Today + 5 more days = 6 days total
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
            
            // Fetch data for initial (today) selection
            fetchHourlyData(today.toISOString().split('T')[0]);
            
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
                fetch(`/api/hourly_wind_data?date=${selectedDate}&plant_id=${plantId}`)
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
                                                Showing wind generation forecast for <strong>${daysInFuture} day${daysInFuture > 1 ? 's' : ''} in the future</strong>. Actual values will be recorded once this date arrives.
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
            fetch(`/api/wind_chart_data?plant_id=${plantId}`)
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
                            borderColor: '#7f7fd5',
                            borderWidth: 1
                        },
                        {
                            label: 'Actual Generation (kWh)',
                            data: dailyActuals,
                            backgroundColor: 'rgba(145, 234, 228, 0.7)',
                            borderColor: '#91eae4',
                            borderWidth: 1
                        },
                        {
                            label: 'Threshold',
                            data: dailyThresholds,
                            type: 'line',
                            borderColor: '#6366f1',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            fill: false,
                            pointStyle: false
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
    
    // Initialize efficiency pie chart
    const efficiencyChartCanvas = document.getElementById('efficiencyChart');
    if (efficiencyChartCanvas) {
        // Default value if no data available
        let latestEfficiency = 0;
        let remainingPercentage = 100;
        
        // Get the latest efficiency value if available
        if (efficiencyData && efficiencyData.length > 0) {
            latestEfficiency = efficiencyData[0]; 
        } else if (dailyPredictions.length > 0 && dailyThresholds.length > 0) {
            // Calculate efficiency from daily data (use the most recent data point)
            latestEfficiency = Math.round((dailyPredictions[0] / dailyThresholds[0]) * 100);
        } else {
            // Use a placeholder for demo purposes
            latestEfficiency = 65; // Default demo value
        }
        
        // Ensure efficiency is between 0 and 100
        latestEfficiency = Math.max(0, Math.min(100, latestEfficiency));
        remainingPercentage = 100 - latestEfficiency;
        
        const efficiencyChart = new Chart(efficiencyChartCanvas, {
            type: 'doughnut',
            data: {
                labels: ['Current Efficiency', 'Remaining'],
                datasets: [{
                    data: [latestEfficiency, remainingPercentage],
                    backgroundColor: [
                        latestEfficiency > 90 ? '#7f7fd5' :
                        latestEfficiency > 70 ? '#86a8e7' :
                        '#91eae4',
                        '#e2e8f0'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: '70%',
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                return context.label + ': ' + context.raw + '%';
                            }
                        }
                    }
                }
            }
        });
        
        // Add center text displaying the percentage
        Chart.register({
            id: 'centerText',
            afterDraw: function(chart) {
                const width = chart.width;
                const height = chart.height;
                const ctx = chart.ctx;
                
                ctx.restore();
                const fontSize = (height / 100).toFixed(2);
                ctx.font = fontSize + 'em sans-serif';
                ctx.textBaseline = 'middle';
                ctx.textAlign = 'center';
                
                const text = latestEfficiency + '%';
                const textX = width / 2;
                const textY = height / 2;
                
                ctx.fillStyle = latestEfficiency > 90 ? '#7f7fd5' :
                               latestEfficiency > 70 ? '#86a8e7' :
                               '#91eae4';
                ctx.fillText(text, textX, textY);
                ctx.save();
            }
        });
    }

    // Refresh button functionality
    const refreshButton = document.getElementById('refreshData');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            // Show loading state
            this.disabled = true;
            this.innerHTML = `
                <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Refreshing...
            `;

            // Make AJAX request to refresh data
            fetch('/api/refresh-wind-data')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Reload the page to show new data
                        window.location.reload();
                    } else {
                        alert('Error refreshing data: ' + data.message);
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
                    alert('An error occurred while refreshing data.');
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

// Function to fetch and display weather data
function fetchWeatherData() {
    const weatherDataContainer = document.getElementById('weather-data');
    const windSpeedEl = document.getElementById('wind-speed');
    const windImpactEl = document.getElementById('wind-impact');
    
    if (!weatherDataContainer) return;

    fetch('/api/weather-data')
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const weather = data.data;
                
                // Update wind speed element
                if (windSpeedEl) {
                    windSpeedEl.textContent = weather.wind_speed + ' km/h';
                }
                
                // Update wind impact element
                if (windImpactEl) {
                    if (weather.wind_speed > 25) {
                        windImpactEl.textContent = 'Optimal wind generation conditions';
                        windImpactEl.className = 'text-sm text-green-500';
                    } else if (weather.wind_speed > 10) {
                        windImpactEl.textContent = 'Good wind generation conditions';
                        windImpactEl.className = 'text-sm text-blue-500';
                    } else {
                        windImpactEl.textContent = 'Low wind conditions';
                        windImpactEl.className = 'text-sm text-yellow-500';
                    }
                }
                
                weatherDataContainer.innerHTML = `
                    <div class="text-center p-4 bg-wind-light rounded-lg">
                        <div class="text-4xl mb-2">
                            ${getWeatherIcon(weather.condition)}
                        </div>
                        <p class="font-semibold wind-text-primary">${weather.condition}</p>
                        <p class="text-gray-600">${weather.temperature}°C</p>
                    </div>
                    <div class="text-center p-4 bg-wind-light rounded-lg">
                        <div class="text-2xl mb-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto wind-text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
                            </svg>
                        </div>
                        <p class="font-semibold wind-text-primary">Wind Speed</p>
                        <p class="text-gray-600">${weather.wind_speed} km/h</p>
                    </div>
                    <div class="text-center p-4 bg-wind-light rounded-lg">
                        <div class="text-2xl mb-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto wind-text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
                            </svg>
                        </div>
                        <p class="font-semibold wind-text-primary">Wind Direction</p>
                        <p class="text-gray-600">${weather.wind_direction || 'N/A'}</p>
                    </div>
                    <div class="text-center p-4 bg-wind-light rounded-lg">
                        <div class="text-2xl mb-2">
                            <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 mx-auto wind-text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
                            </svg>
                        </div>
                        <p class="font-semibold wind-text-primary">Cloud Cover</p>
                        <p class="text-gray-600">${weather.cloud_cover || weather.cloudCover || '0'}%</p>
                    </div>
                `;
            } else {
                weatherDataContainer.innerHTML = `
                    <div class="col-span-4 text-center p-4 bg-wind-light rounded-lg border border-red-300">
                        <p class="text-red-700">Error loading weather data: ${data.message}</p>
                    </div>
                `;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            weatherDataContainer.innerHTML = `
                <div class="col-span-4 text-center p-4 bg-wind-light rounded-lg border border-red-300">
                    <p class="text-red-700">Failed to load weather data. Please try again later.</p>
                </div>
            `;
        });
}

// Helper function to get weather icon
function getWeatherIcon(condition) {
    condition = condition.toLowerCase();
    if (condition.includes('sunny') || condition.includes('clear')) {
        return '☀️';
    } else if (condition.includes('cloud')) {
        return '⛅';
    } else if (condition.includes('rain')) {
        return '🌧️';
    } else if (condition.includes('storm') || condition.includes('thunder')) {
        return '⛈️';
    } else if (condition.includes('snow')) {
        return '❄️';
    } else if (condition.includes('fog') || condition.includes('mist')) {
        return '🌫️';
    } else {
        return '🌤️';
    }
} 