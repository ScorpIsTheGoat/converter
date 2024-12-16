document.addEventListener("DOMContentLoaded", async () => {
    const filePath = window.location.pathname;
    const fileHash = filePath.split("/").pop(); 

    if (!fileHash) {
        document.getElementById("content-display").innerHTML = "<p>No file hash provided.</p>";
        return;
    }

    try {
        // Fetch metadata and file content
        const metadataResponse = await fetch(`/file/${fileHash}`);
        if (!metadataResponse.ok) {
            throw new Error("File not found");
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