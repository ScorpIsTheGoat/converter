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
            document.getElementById('format').style.display = 'block';
            document.getElementById('convert-btn').style.display = 'block'; 
            document.getElementsByClassName('dropdown')[0].style.display = 'block';
        }
        return response.json();
    })
    .then(data => console.log(data))
    .catch(error => console.error('Error:', error));
});

document.getElementById('convert-btn').addEventListener('click', async function (event) {
    event.preventDefault();
    console.log("Convert Button has been clicked")
    let filetypeToConvertTo = document.getElementById('format').value;
    let videocodecToConvertTo = document.getElementById('videocodec').value;
    let audiocodecToConvertTo = document.getElementById('audiocodec').value;
    let videobitrateToConvertTo = document.getElementById('videobitrate').value;
    let audiobitrateToConvertTo = document.getElementById('audiobitrate').value;
    let resoultionToConvertTo = document.getElementById('resolution').value;
    let framerateToConvertTo = document.getElementById('framerate').value;
    console.log(filetypeToConvertTo);
    LOGS.innerHTML = "Converting to " + filetypeToConvertTo;

    try {
        let response = await fetch('/convert', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                filetype: filetypeToConvertTo,
                videocodec: videocodecToConvertTo,
                audiocodec: audiocodecToConvertTo,
                videobitrate: videobitrateToConvertTo,
                audiobitrate: audiobitrateToConvertTo,
                resolution: resoultionToConvertTo,
                framerate: framerateToConvertTo
            })
        });

        if (!response.ok) {
            throw new Error('Network response was not ok ' + response.statusText);
        }

        let blob = await response.blob();
        let url = window.URL.createObjectURL(blob);
        let a = document.createElement('a');
        a.href = url;
        a.download = `converted_file.${filetypeToConvertTo}`;
        a.id = 'download-link';
        
        document.body.appendChild(a); // Append the link to the body
        document.getElementById('download-btn').style.display = 'block'; // Show the download button
        document.getElementById('download-btn').onclick = function() {
            a.click(); // Trigger the click on the hidden link
            a.remove(); // Remove the link from the DOM after clicking
        };

        logs.innerHTML = "Conversion successful! Click the button to download.";
    } catch (error) {
        logs.innerHTML = "Conversion failed: " + error.message;
    }
});
function toggleDropdown() {
    document.getElementsByClassName("dropdown-content")[0].classList.toggle("show");
}


