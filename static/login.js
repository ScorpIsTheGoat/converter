document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent default form submission

    // Retrieve username and password from input fields
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    console.log('Username:', username);
    console.log('Password:', password);

    try {
        // Make POST request to /login-post
        let response = await fetch('/login-post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                username: username,
                password: password,
            }),
            credentials: 'include'  // Ensure cookies are included in the request
        });

        if (response.ok) {
            const data = await response.json();
            console.log('Login successful:', data);

            // Check for the 'session_id' cookie and redirect to "/" if set
            if (document.cookie.includes('session_id')) {
                console.log('Session ID cookie found. Redirecting to "/"...');
                window.location.href = '/';
            } else {
                console.error('Session ID cookie not found. Login failed.');
            }
        } else {
            const errorData = await response.json();
            console.error('Login failed:', errorData.detail);
        }
    } catch (error) {
        console.error('Error during login:', error);
    }
});