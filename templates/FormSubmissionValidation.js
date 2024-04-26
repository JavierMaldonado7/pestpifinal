document.getElementById('loginForm').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent form submission

    // Get user input
    var username = document.getElementById('username').value; // Assuming you have a username field
    var password = document.getElementById('password').value;

    // Example validation (you should perform proper validation)
    if (username.trim() === '' || password.trim() === '') {
        document.getElementById('error-msg').innerText = 'Please enter both username and password.';
        return;
    }

    // Send data to server for validation (using AJAX)
    var xhr = new XMLHttpRequest();
    xhr.open('POST', '/login', true);  // Update the URL to your Flask route
    xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    xhr.onload = function() {
        if (xhr.status === 200) {
            var response = JSON.parse(xhr.responseText);
            if (response.success) {
                // Redirect to dashboard or perform further actions
                window.location.href = '/dashboard'; // Update with your actual dashboard URL
            } else {
                document.getElementById('error-msg').innerText = response.message;
            }
        } else {
            document.getElementById('error-msg').innerText = 'Login failed. Please try again.';
        }
    };
    xhr.send('username=' + encodeURIComponent(username) + '&password=' + encodeURIComponent(password));

});
