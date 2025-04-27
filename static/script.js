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
    const logo = document.querySelector(".logo");
    const uploadBtn = document.getElementById("upload-btn")
    const convertBtn = document.getElementById("convert-btn")
    const container = document.querySelector(".container");
    const authButtons = document.querySelector(".auth-buttons");
    const funcButtons = document.querySelector(".func-buttons");
    const profileIconContainer = document.getElementById("profile-icon-container");
    // If session_id exists, the user is logged in, so add the animation
    if (sessionId) {
        if (container) container.style.display = "none";
        if (authButtons) authButtons.style.display = "none";
        // Add the logo animation when user is logged in
        if (logo) {
            logo.classList.add("float-to-top-left");
        }
        funcButtons.style.display = "flex"; // Show func buttons
        uploadBtn.classList.add("float-in-top")
        
        if (profileIconContainer) {
            const profileIconWrapper = document.createElement("div");
            profileIconWrapper.style.display = "flex";
            profileIconWrapper.style.alignItems = "center"; // Align the icon and name
            profileIconWrapper.style.gap = "10px";

            const profileIcon = document.createElement("div");
            profileIcon.classList.add("profile-icon");
            profileIcon.innerHTML = "👤"; // You can replace this with an image or icon
            profileIcon.style.marginRight = "8px"; // Space between icon and name

            const dropdownMenu = document.getElementById("dropdown-menu"); // Get the dropdown from HTML
            dropdownMenu.style.display = "none"; // Initially hide the dropdown
            
            // Fetch the username from the backend
            fetch(`/get-username-by-session?session_id=${sessionId}`)
                .then(response => response.json())
                .then(data => {
                    const userName = data.username || "User"; // Default to "User" if no name is found
                    const userNameElement = document.createElement("span");
                    userNameElement.classList.add("user-name");
                    userNameElement.innerText = userName;

                    // Append the username next to the profile icon
                    profileIconWrapper.appendChild(userNameElement);
                    profileIconWrapper.appendChild(profileIcon);
                    profileIconContainer.appendChild(profileIconWrapper);

                    // Position the profile icon and name at the top-right
                    profileIconWrapper.style.position = "absolute";
                    profileIconWrapper.style.top = "10px"; // Adjust as needed
                    profileIconWrapper.style.right = "10px"; // Adjust as needed
                    profileIconWrapper.style.cursor = "pointer";
                    dropdownMenu.style.display = "none";
                    // Show dropdown menu on hover

                    profileIconContainer.addEventListener("mouseenter", () => {
                        dropdownMenu.style.display = "block"; // Show dropdown
                        userNameElement.classList.add("active");
                    });

                    // Prevent dropdown from hiding when hovering over the dropdown itself

                    dropdownMenu.addEventListener("mouseleave", () => {
                        dropdownMenu.style.display = "none"; // Hide dropdown when mouse leaves dropdown
                        userNameElement.classList.remove("active"); // Reset username color
                    });
                    
                })
                .catch(error => {
                    console.error("Error fetching username:", error);
                });
        }
    } else {
        if (logo) logo.classList.remove("float-to-top-left");
    }
});

document.getElementById("logout-link").addEventListener("click", function(event) {
    event.preventDefault();  // Prevent default anchor behavior (navigating to the link)
    
    // Send the POST request to logout the user
    fetch("/logout", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        credentials: "same-origin",  // Send cookies with the request
    })
    .then(response => {
        if (response.ok) {
            window.location.href = "/";  // Redirect to home after successful logout
        } else {
            console.error("Logout failed.");
        }
    })
    .catch(error => {
        console.error("Error during logout:", error);
    });
});
