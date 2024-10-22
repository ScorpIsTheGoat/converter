document.getElementById('loginForm').addEventListener('submit', async function(event) {
    event.preventDefault(); 

    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;

    console.log(username)
    console.log(password)
    try {
        let response = await fetch('/login-post', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                username: username,
                password: password,
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
        console.log(error);
    }
});