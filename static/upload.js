document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();

    const files = document.getElementById('fileInput').files;
    if (files.length === 0) {
        alert('Please select at least one file.');
        return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        const response = await fetch('/upload-post', {
            method: 'POST',
            body: formData,
        });

        if (response.ok) {
            document.getElementById('status').textContent = 'Files uploaded successfully!';
        } else {
            document.getElementById('status').textContent = 'Failed to upload files.';
        }
    } catch (error) {
        console.error('Error uploading files:', error);
        document.getElementById('status').textContent = 'An error occurred while uploading files.';
    }
});
