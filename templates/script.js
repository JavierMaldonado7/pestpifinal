document.addEventListener('DOMContentLoaded', function() {
    const contentDiv = document.querySelector('.content');
    const menuItems = document.querySelectorAll('.menu-item:not(.logout-button)');

    menuItems.forEach(item => {
        item.addEventListener('click', function(event) {
            event.preventDefault();
            setActiveMenuItem(item);
            updateContentBasedOnMenuItem(item);
        });
    });

    // Load 'Alerts' by default
    document.querySelector('.menu-item').click();

    function setActiveMenuItem(selectedItem) {
        menuItems.forEach(item => item.classList.remove('active'));
        selectedItem.classList.add('active');
    }

    function updateContentBasedOnMenuItem(item) {
        switch (item.textContent.trim()) {
            case 'Alerts':
                updateContentToAlerts();
                break;
            case 'Statistics':
                updateContentToStatistics();
                break;
            case 'Camera':
                updateContentToCamera();
                break;
            case 'Settings':
                updateContentToSettings();
                break;
        }
    }

    function updateContentToAlerts() {
        contentDiv.innerHTML = `
            <div id="alertModal" class="modal">
                <div class="modal-content">
                    <span class="close">&times;</span>
                    <img id="alertImage" style="width:100%;" />
                </div>
            </div>
            <div id="head_">Alerts</div>
            <div class="dashboard-container">
                <div class="left-section">
                    <div class="cards-container">
                        <div class="card card-iguana">
                            <div class="card-title">Iguana</div>
                            <div class="card-count" id="iguana-count">Loading...</div>
                        </div>
                        <div class="card card-rodent">
                            <div class="card-title">Rodent</div>
                            <div class="card-count" id="rodent-count">Loading...</div>
                        </div>
                        <div class="card card-boa">
                            <div class="card-title">Boa</div>
                            <div class="card-count" id="boa-count">Loading...</div>
                        </div>
                    </div>
                    <div class="alerts-section">
                        <table id="alerts-table">
                            <thead>
                                <tr>
                                    <th>Type</th>
                                    <th>Date</th>
                                    <th>Location</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody id="alerts-tbody">
                                <!-- Alerts will be inserted here by JavaScript -->
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="filter-menu">
                    <h2>Filter Alerts</h2>
                    <select id="alert-type-select" class="filter-select">
                        <option value="all">All Types</option>
                        <option value="Iguana">Iguana</option>
                        <option value="Rodent">Rodent</option>
                        <option value="Boa">Boa</option>
                    </select>
                    <select id="alert-date-select" class="filter-select">
                        <option value="all">All Dates</option>
                        <option value="today">Today</option>
                        <option value="this_week">This Week</option>
                        <option value="this_month">This Month</option>
                    </select>
                    <select id="alert-location-select" class="filter-select">
                        <option value="all">All Locations</option>
                        <!-- Options will be inserted here by JavaScript -->
                    </select>
                    <button type="button" id="apply-filters-btn" class="apply-filters-btn">Apply Filters</button>
                    <button onclick="fetchAndDisplayAlerts()" class="refresh-alerts-btn">Refresh Alerts</button>
                </div>
            </div>
        `;
        document.getElementById('apply-filters-btn').addEventListener('click', applyFilters);
        document.getElementById('alerts-tbody').addEventListener('click', handleAlertButtonClick);
    }

    function applyFilters(event) {
        event.preventDefault();

        const alertType = document.getElementById('alert-type-select').value;
        const alertDate = document.getElementById('alert-date-select').value;
        const alertLocation = document.getElementById('alert-location-select').value;

        let apiEndpoint = `/api/filter?`;
        let queryParams = [];
        if (alertType !== 'all') queryParams.push(`type=${alertType}`);
        if (alertDate !== 'all') queryParams.push(`date=${alertDate}`);
        if (alertLocation !== 'all') queryParams.push(`location=${alertLocation}`);

        apiEndpoint += queryParams.join('&');

        fetch(apiEndpoint)
            .then(response => response.json())
            .then(alerts => {
                const alertsTableBody = document.getElementById('alerts-tbody');
                alertsTableBody.innerHTML = '';
                alerts.forEach(alert => {
                    const row = `
                        <tr>
                            <td>${alert.alert_type}</td>
                            <td>${alert.alert_date}</td>
                            <td>${alert.alert_location}</td>
                            <td>
                                <button class="view-image-btn" data-alert-id="${alert.alert_id}">View Image</button>
                                <button class="remove-alert-btn" data-alert-id="${alert.alert_id}">Remove</button>
                            </td>
                        </tr>`;
                    alertsTableBody.innerHTML += row;
                });
            })
            .catch(error => console.error('Error applying filters:', error));
    }

    function updateContentToStatistics() {
        contentDiv.innerHTML = `
            <div id="head_">Statistics</div>
            <div class="filter-menu-stats">
                <h2>Filter Statistics</h2>
                <div class="filter-options">
                    <select id="stats-location-select" class="filter-select">
                        <option value="most_frequent">Most Frequent Locations</option>
                        <!-- Additional options can be added here -->
                    </select>
                    <!-- Add more dropdowns for other statistics options if needed -->
                </div>
            </div>
            <div class="chart-container">
                <canvas id="locationPieChart"></canvas>
            </div>
        `;
        drawCharts();
        document.getElementById('stats-location-select').addEventListener('change', function() {
            drawCharts(this.value);
        });
    }

    function drawCharts(filter = 'most_frequent') {
        fetch(`/api/location_stats?location=${filter}`)
            .then(response => response.json())
            .then(data => {
                const ctxPie = document.getElementById('locationPieChart').getContext('2d');
                const topLocations = data.slice(0, 5).map(d => d.location);
                const topCounts = data.slice(0, 5).map(d => d.count);
                if (window.pieChart) window.pieChart.destroy();
                window.pieChart = new Chart(ctxPie, {
                    type: 'pie',
                    data: {
                        labels: topLocations,
                        datasets: [{
                            label: 'Alert Counts',
                            data: topCounts,
                            backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56', '#cc65fe', '#ff9f40']
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        legend: {
                            position: 'bottom',
                            labels: {
                                fontColor: 'black',
                                fontSize: 14
                            }
                        },
                        title: {
                            display: true,
                            text: 'Top 5 Location Statistics',
                            fontColor: 'black',
                            fontSize: 18
                        }
                    }
                });
            })
            .catch(error => console.error('Error fetching location statistics:', error));
    }
});
