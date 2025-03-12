// Handle login form submission
document.getElementById('loginForm').addEventListener('submit', function(e) {
    e.preventDefault();  // Prevent the form from submitting the traditional way

    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;

    // Log for debugging
    console.log('Attempting to log in with:', email, password);

    // Send login data to Flask using fetch
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email, password: password })
    })
    .then(response => response.json())  // Parse JSON response
    .then(data => {
        console.log('Server response:', data);

        // Handle success or failure
        if (data.message === 'Login successful!') {
            window.location.href = data.redirect;  // Redirect to home after successful login
        } else {
            alert(data.message);  // Show error message from Flask
        }
    })
    .catch(error => {
        console.error('Login error:', error);
        alert('Something went wrong. Please try again.');
    });
});
