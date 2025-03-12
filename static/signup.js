// signup.js

document.addEventListener('DOMContentLoaded', function() {
    const signupForm = document.getElementById('signupForm');
    
    signupForm.addEventListener('submit', function(event) {
        event.preventDefault();  // Prevent form from submitting normally

        // Get form values
        const name = document.getElementById('name').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;

        // Create data object
        const formData = {
            name: name,
            email: email,
            password: password
        };

        // Send the data using AJAX (fetch API)
        fetch('/signup', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(formData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                // Display success or error message
                const alertBox = document.createElement('div');
                alertBox.className = 'alert alert-info';
                alertBox.innerText = data.message;
                document.body.appendChild(alertBox);
                
                // Redirect to login page on successful signup
                if (data.redirect) {
                    window.location.href = data.redirect;
                }
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
});
