
const path = window.location.pathname; // e.g., "/file/asfasdfvasdvfaw45tpuihsededrpoit"
const fileHash = path.split("/file/")[1];

// Get elements
const videoPlayer = document.getElementById("videoPlayer");
const loadingMessage = document.getElementById("loadingMessage");
const videoFileName = document.getElementById("videoFileName");

// Show loading message
loadingMessage.style.display = "block";

// Fetch and set the video source
const videoUrl = `/file/content/${fileHash}`;
videoPlayer.src = videoUrl; // Set video source directly
videoFileName.textContent = `Now playing: ${fileHash}`; // Display the hash as the file name

// Handle video load events
videoPlayer.oncanplay = function () {
    loadingMessage.style.display = "none"; // Hide loading message when the video is ready to play
};

videoPlayer.onerror = function () {
    loadingMessage.textContent = "Failed to load video. Please try again later.";
};
