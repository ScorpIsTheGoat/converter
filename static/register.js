document.getElementById('registerForm').addEventListener('submit', async function(event) {
    event.preventDefault(); 

    var username = document.getElementById('username').value;
    var email = document.getElementById('email').value;
    var password = document.getElementById('password').value;
    var confirmPassword = document.getElementById('confirm-password').value;
    console.log(username)
    console.log(email)
    console.log(password)
    console.log(confirmPassword)
    try {
        let response = await fetch('/register-post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                username: username,
                email: email,
                password: password,
                confirmPassword: confirmPassword
            })
        });
        if (response.redirected) {
            // If the response contains a redirect, manually follow it
            window.location.href = response.url;
        }
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }
    } catch (error) {
        LOGS.innerHTML = "Conversion failed: " + error.message;
    }
});
