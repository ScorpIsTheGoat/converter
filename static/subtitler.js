const LOGS = document.getElementById('logs');
document.getElementById('file').addEventListener('change', async function(event) {
    event.preventDefault();
    LOGS.innerHTML ='';
    const fileInput = document.getElementById('file');
    LOGS.innerHTML += 'File Input:' + fileInput.value + '\n';

    const file = fileInput.files[0];
    LOGS.innerHTML += 'Selected File:' + file.name + '\n'; 
    
    const formData = new FormData();
    formData.append('file', file);
    
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (response.ok) {
            LOGS.innerHTML= "uploaded successfully"
            console.log('Worked');
            document.getElementById('subtitleForm').style.display = 'block';
            document.getElementById('convert-btn').style.display = 'block'; 
        }
        return response.json();
    })
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
});

document.getElementById('convert-btn').addEventListener('click', async function (event) {
    event.preventDefault();
    document.getElementById('convert-btn').style.display = 'none'; 
    console.log("Convert Button has been clicked")
    let language = document.getElementById('language').value;
    let model = document.getElementById('model').value;
    let task = document.getElementById('task').value;
    console.log(language, model, task)
    LOGS.innerHTML = "Adding"

    try {
        let response = await fetch('/give', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                language: language,
                model: model,
                task: task
            })
        });
        console.log(response)
        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }

        let blob = await response.blob();
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        a.href = url;
        a.download = `converted_file.mp4`;
        a.id = 'download-link';
        
        document.body.appendChild(a); 
        document.getElementById('download-btn').style.display = 'block'; 
        document.getElementById('download-btn').onclick = function() {
            a.click(); 
            a.remove(); 
        };

        logs.innerHTML = "Conversion successful! Click the button to download.";
    } catch (error) {
        logs.innerHTML = "Conversion failed: " + error.message;
    }
});
function toggleDropdown() {
    document.getElementsByClassName("dropdown-content")[0].classList.toggle("show");
}


