const ctx = document.getElementById('alertsChart').getContext('2d');
const alertsChart = new Chart(ctx, {
    type: 'line', // Change this type as needed (bar, pie, etc.)
    data: {
        labels: [], // To be filled dynamically
        datasets: [{
            label: 'Number of Alerts',
            data: [], // To be filled dynamically
            backgroundColor: [
                'rgba(255, 99, 132, 0.2)'
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

fetch('/api/alerts')
    .then(response => response.json())
    .then(data => {
        alertsChart.data.labels = data.dates;
        alertsChart.data.datasets[0].data = data.counts;
        alertsChart.update();
    })
    .catch(error => console.error('Error fetching alert data:', error));
