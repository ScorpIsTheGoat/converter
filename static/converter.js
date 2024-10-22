//upload
document.getElementById('file').addEventListener('change', async function(event) {
    event.preventDefault();
    document.getElementById('convert-btn').style.display = 'block'; 
    const fileInput = document.getElementById('file');
    const formData = new FormData();
    const files = fileInput.files;
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]); // Append each file, debugger says formData is empty, but I still receive somthing on the backend
    }
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = ''; 
    //displaying uploaded files
    Array.from(files).forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.classList.add('file-item');
        const fileTitle = document.createElement('h3');
        fileTitle.textContent = file.name;
        const fileDetails = document.createElement('p');
        fileDetails.classList.add('file-details');
        fileDetails.textContent = `Size: ${(file.size / 1024 / 1024).toFixed(2)} MB | Type: ${file.type}`;
        const formatSelect = document.createElement('select');
        formatSelect.name = `format-${file.name}`;
        formatSelect.innerHTML = `
            <option value="mp4">mp4</option>
            <option value="mov">mov</option>
            <option value="avi">avi</option>
            <option value="mkv">mkv</option>
            <option value="flv">flv</option>
            <option value="wmv">wmv</option>
            <option value="webm">webm</option>
            <option value="mp3">mp3</option>
            <option value="aac">aac</option>
            <option value="wav">wav</option>
            <option value="ogg">ogg</option>
            <option value="gif">gif</option>
        `;
        fileItem.appendChild(fileTitle);
        fileItem.appendChild(fileDetails);
        fileItem.appendChild(formatSelect);
        
        // Append file item to the grid
        fileList.appendChild(fileItem);
    });
    //should be able to send multiple files at once to backend but doesn't work (422 unprocessable entity)
    try {
        const response = await fetch('/converter-upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        console.log('Upload successful:', data);
    } catch (error) {
        console.error('Error during file upload:', error);
    }
});

document.getElementById('convert-btn').addEventListener('click', async function (event) {
    event.preventDefault();
    document.getElementById('subtitleForm').style.display = 'none'
    document.getElementById('convert-btn').style.display = 'none'; 
    document.getElementsByClassName('dropdown')[0].style.display = 'block';
    console.log("Convert Button has been clicked")
    let filetypeToConvertTo = document.getElementById('format').value;
    let videocodecToConvertTo = document.getElementById('videocodec').value;
    let audiocodecToConvertTo = document.getElementById('audiocodec').value;
    let videobitrateToConvertTo = document.getElementById('videobitrate').value;
    let audiobitrateToConvertTo = document.getElementById('audiobitrate').value;
    let resoultionToConvertTo = document.getElementById('resolution').value;
    let framerateToConvertTo = document.getElementById('framerate').value;
    console.log(filetypeToConvertTo);
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

    } catch (error) {
        console.log("Error occured")
    }
});
function toggleDropdown() {
    document.getElementsByClassName("dropdown-content")[0].classList.toggle("show");
}


