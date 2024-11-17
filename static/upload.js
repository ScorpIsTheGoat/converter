document.getElementById('file').addEventListener('change', async function(event) {
    event.preventDefault();
    const fileInput = document.getElementById('file');
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    fetch('/upload-post', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            LOGS.innerHTML= "uploaded successfully"
            console.log('Worked');
        }
        return response.json();
    })
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
});