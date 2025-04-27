document.addEventListener("DOMContentLoaded", async () => {
    const filePath = window.location.pathname;
    const fileHash = filePath.split("/").pop(); 

    if (!fileHash) {
        document.getElementById("content-display").innerHTML = "<p>No file hash provided.</p>";
        return;
    }

    try {
        // Fetch metadata and file content
        const metadataResponse = await fetch(`/metadata/${fileHash}`);
        if (!metadataResponse.ok) {
            throw new Error("File not found");
        }
        const metadata = await metadataResponse.json();

        // Get the metadata object (assuming it is under 'metadata' key)
        const validMetadata = metadata.metadata;

        // Get the metadata display container
        const metadataDisplay = document.getElementById("metadata-display");


        // Check each key in the metadata and display it
        for (const key in validMetadata) {
            if (validMetadata.hasOwnProperty(key)) {
                const element = document.getElementById(key);
                value = validMetadata[key];
                if (key === "FileSize") {
                    // Convert bytes to MB or GB
                    if (value >= 1073741824) { // If the value is greater than or equal to 1 GB
                        value = (value / 1073741824).toFixed(2) + " GB";
                    } else if (value >= 1048576) { // If the value is greater than or equal to 1 MB
                        value = (value / 1048576).toFixed(2) + " MB";
                    } else if (value >= 1024) { // If the value is greater than or equal to 1 KB
                        value = (value / 1024).toFixed(2) + " KB";
                    } else {
                        value = value + " bytes"; // Just show bytes if the value is too small
                    }
                }
                if (key === "Duration" && value !== "none") {
                    const totalSeconds = parseInt(value, 10); // Ensure the value is an integer
                    const hours = Math.floor(totalSeconds / 3600);
                    const minutes = Math.floor((totalSeconds % 3600) / 60);
                    const seconds = totalSeconds % 60;
                    value = `${hours > 0 ? (hours < 10 ? '0' + hours : hours) + ':' : ''}${minutes < 10 ? '0' + minutes : minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
                }
                // Set the innerHTML of the element if it exists
                if (element) {
                    // Handle null or undefined values
                    element.innerHTML += value
                }
            }
        }
        const contentResponse = await fetch(`/file/content/${fileHash}`);
        const contentType = contentResponse.headers.get("Content-Type");

        const contentDisplay = document.getElementById("content-display");
        if (contentType.startsWith("video/")) {
            const video = document.createElement("video");
            video.src = `/file/content/${fileHash}`;
            video.controls = true;
            contentDisplay.appendChild(video);
        } else if (contentType.startsWith("image/")) {
            const img = document.createElement("img");
            img.src = `/file/content/${fileHash}`;
            contentDisplay.appendChild(img);
        } else if (contentType.startsWith("text/")) {
            const text = await contentResponse.text();
            const pre = document.createElement("pre");
            pre.textContent = text;
            contentDisplay.appendChild(pre);
        }  else if (contentType.startsWith("audio/")) {
            const audio = document.createElement("audio");
            audio.src = `/file/content/${fileHash}`;
            audio.controls = true;
            contentDisplay.appendChild(audio);
        } else {
            const fallback = document.createElement("div");
            fallback.id = "fallback-icon";
            fallback.textContent = "📁";
            contentDisplay.appendChild(fallback);
        }
    } catch (error) {
        document.getElementById("content-display").innerHTML = `<p>${error.message}</p>`;
    }
});