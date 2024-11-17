document.addEventListener("DOMContentLoaded", function() {
    const sessionId = getCookie("session_id");
    const authButtonsDiv = document.querySelector(".auth-buttons");

    if (sessionId) {
        fetch("/get-username-by-session", {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.username) {
                    authButtonsDiv.innerHTML = `<button class="button" id="user-btn">${data.username}</button>`;

                    document.getElementById("user-btn").addEventListener('click', function() {
                        window.location.href = `/profile/${data.username}`;
                    });

                    const logoutBtn = document.getElementById("logout-btn");
                    if (logoutBtn) {
                        logoutBtn.addEventListener('click', function() {
                            document.cookie = "session_id=; Max-Age=-99999999;";  // Remove cookie
                            window.location.href = "/";  
                        });
                    }
                }
            })
            .catch(error => {
                console.error("Error fetching username:", error);
            });
    }
    else {
        // If no session, show login/register
        authButtonsDiv.innerHTML = `
            <a href="login" class="button">Login</a>
            <a href="register" class="button">Register</a>
        `;
    }
});


document.getElementById('logout-btn').addEventListener('click', async function() {
    try {
        // Call the backend to logout
        let response = await fetch('/logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        if (response.ok) {
            window.location.href = '/'; 
        } else {
            console.error('Logout failed');
        }
    } catch (error) {
        console.error('Error during logout:', error);
    }
});