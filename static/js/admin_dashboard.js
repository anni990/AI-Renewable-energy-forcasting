document.addEventListener('DOMContentLoaded', function() {
    // Handle tab switching
    const tabs = document.querySelectorAll('.tab-button');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(c => c.classList.add('hidden'));
            
            // Add active class to clicked tab
            tab.classList.add('active');
            
            // Show corresponding content
            const contentId = tab.id.replace('tab-', 'content-');
            document.getElementById(contentId).classList.remove('hidden');
            
            // Adjust charts for proper rendering in previously hidden containers
            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 100);
        });
    });
    
    // Initialize Solar Chart
    const solarChartCanvas = document.getElementById('solarChart');
    if (solarChartCanvas) {
        const solarChart = new Chart(solarChartCanvas, {
            type: 'line',
            data: {
                labels: solarLabels,
                datasets: [
                    {
                        label: 'Predicted Generation (kWh)',
                        data: solarPredictions,
                        borderColor: '#22c55e',
                        backgroundColor: 'rgba(34, 197, 94, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Actual Generation (kWh)',
                        data: solarActuals,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
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
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }
    
    // Initialize Wind Chart
    const windChartCanvas = document.getElementById('windChart');
    if (windChartCanvas) {
        const windChart = new Chart(windChartCanvas, {
            type: 'line',
            data: {
                labels: windLabels,
                datasets: [
                    {
                        label: 'Predicted Generation (kWh)',
                        data: windPredictions,
                        borderColor: '#0ea5e9',
                        backgroundColor: 'rgba(14, 165, 233, 0.1)',
                        borderWidth: 2,
                        tension: 0.3,
                        fill: true
                    },
                    {
                        label: 'Actual Generation (kWh)',
                        data: windActuals,
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.1)',
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
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }
    
    // Initialize Combined Chart
    const combinedChartCanvas = document.getElementById('combinedChart');
    if (combinedChartCanvas) {
        const combinedChart = new Chart(combinedChartCanvas, {
            type: 'bar',
            data: {
                labels: combinedLabels,
                datasets: [
                    {
                        label: 'Solar Energy (kWh)',
                        data: solarTotals,
                        backgroundColor: 'rgba(34, 197, 94, 0.7)',
                        borderColor: '#22c55e',
                        borderWidth: 1,
                        order: 2
                    },
                    {
                        label: 'Wind Energy (kWh)',
                        data: windTotals,
                        backgroundColor: 'rgba(14, 165, 233, 0.7)',
                        borderColor: '#0ea5e9',
                        borderWidth: 1,
                        order: 3
                    },
                    {
                        label: 'Combined Threshold',
                        data: combinedThresholds,
                        type: 'line',
                        borderColor: '#dc2626',
                        borderWidth: 2,
                        borderDash: [5, 5],
                        fill: false,
                        pointStyle: false,
                        order: 1
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
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Total Energy Generation (kWh)'
                        }
                    },
                    x: {
                        stacked: true,
                        title: {
                            display: true,
                            text: 'Date'
                        }
                    }
                }
            }
        });
    }
    
    // Plant selection functionality
    const plantSelect = document.getElementById('plant-select');
    if (plantSelect) {
        plantSelect.addEventListener('change', function() {
            // Show loading state
            const loadingOverlay = document.createElement('div');
            loadingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
            loadingOverlay.innerHTML = `
                <div class="bg-white p-5 rounded-lg shadow-lg flex items-center">
                    <svg class="animate-spin -ml-1 mr-3 h-8 w-8 text-primary-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <span class="text-lg font-medium text-primary-800">Loading data...</span>
                </div>
            `;
            document.body.appendChild(loadingOverlay);

            // Make AJAX request to get filtered data
            fetch(`/api/plant-data?plant_id=${this.value}&date_range=${document.getElementById('date-range').value}`)
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update chart data
                        if (solarChart && data.solar) {
                            solarChart.data.labels = data.solar.labels;
                            solarChart.data.datasets[0].data = data.solar.predictions;
                            solarChart.data.datasets[1].data = data.solar.actuals;
                            solarChart.update();
                        }
                        
                        if (windChart && data.wind) {
                            windChart.data.labels = data.wind.labels;
                            windChart.data.datasets[0].data = data.wind.predictions;
                            windChart.data.datasets[1].data = data.wind.actuals;
                            windChart.update();
                        }
                        
                        if (combinedChart && data.combined) {
                            combinedChart.data.labels = data.combined.labels;
                            combinedChart.data.datasets[0].data = data.combined.solarTotals;
                            combinedChart.data.datasets[1].data = data.combined.windTotals;
                            combinedChart.data.datasets[2].data = data.combined.thresholds;
                            combinedChart.update();
                        }
                        
                        // Remove loading state
                        document.body.removeChild(loadingOverlay);
                    } else {
                        alert('Error loading data: ' + data.message);
                        // Remove loading state
                        document.body.removeChild(loadingOverlay);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('An error occurred while loading data.');
                    // Remove loading state
                    document.body.removeChild(loadingOverlay);
                });
        });
    }
    
    // Date range selection functionality
    const dateRangeSelect = document.getElementById('date-range');
    if (dateRangeSelect) {
        dateRangeSelect.addEventListener('change', function() {
            if (plantSelect) plantSelect.dispatchEvent(new Event('change'));
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
            fetch('/api/refresh-all-data')
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
});