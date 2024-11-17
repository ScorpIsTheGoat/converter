document.addEventListener("DOMContentLoaded", function() {
    // Function to get the value of a cookie by name
    function getCookie(name) {
        const cookieArr = document.cookie.split(";");
        for (let i = 0; i < cookieArr.length; i++) {
            let cookie = cookieArr[i].trim();
            if (cookie.startsWith(name + "=")) {
                return cookie.substring(name.length + 1);
            }
        }
        return null;
    }

    const sessionId = getCookie("session_id");
    authButtonsDiv = document.querySelector(".auth-buttons");
    const loginBtn = document.getElementById("login-btn");
    const registerBtn = document.getElementById("register-btn");

    // If session_id exists, the user is logged in, so hide login/register buttons
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
                    // Replace login/register buttons with the username button
                    authButtonsDiv.innerHTML = '';
                    userBtn = document.createElement("button");
                    userBtn.classList.add("button");
                    userBtn.id = "user-btn";
                    userBtn.textContent = data.username;

                    // Append the button to the auth-buttons container
                    authButtonsDiv.appendChild(userBtn);                    
                    // Optionally, add functionality to the username button
                    userBtn = document.getElementById("user-btn");
                    userBtn.addEventListener('click', function() {
                        window.location.href = `/profile/${data.username}`;  // Redirect to profile page
                    });
                }
            })
            .catch(error => {
                console.error("Error fetching username:", error);
            });
    } else {
        // Otherwise, show the login/register buttons
        loginBtn.style.display = "block";
        registerBtn.style.display = "block";
    }
});