const videoWrapper = document.getElementsByClassName('video-wrapper');
const videoInput = document.getElementById('videoInput');
const controls = document.getElementsByClassName('controls')[0];
const controlButtons = document.querySelectorAll('.controls button'); 
const colorgradeButton = document.getElementById('colorgrade-button') 

async function sendSelectedFilter(filterId) {
    try {
        const response = await fetch('/colorgrader/type', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ filter_id: filterId }),
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        console.log('Filter sent successfully');
    } catch (error) {
        console.error('Error sending filter:', error);
    }
}

videoInput.addEventListener('change', async function(event) {
    event.preventDefault();  
    videoWrapper[0].style.display = 'block';
    videoInput.style.display = 'none';
    controls.style.display = 'block';
    document.getElementsByClassName('video-controls')[0].style.display = 'block';
    selectedVideoFile = videoInput.files[0];
    extractRandomFrame(URL.createObjectURL(selectedVideoFile));
    const formData = new FormData(); 
    formData.append('video', selectedVideoFile);
    const uploadResponse = fetch('/colorgrader/upload', {
        method: 'POST',
        body: formData
    });
});

controlButtons.forEach(button => {
    button.addEventListener('click', () => {
        controlButtons.forEach(btn => btn.classList.remove('selected-button'));
        button.classList.add('selected-button');
        sendSelectedFilter(button.id);
    });
});

colorgradeButton.addEventListener('click', async () => {
    try {
        const response = await fetch('/colorgrader/confirmation', {
            method: 'POST'
        });

        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const blob = await response.blob();

        const url = window.URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url; 
        a.download = 'processed_image.jpg'; 
        document.body.appendChild(a); 
        a.click();
        a.remove(); 
        setTimeout(() => {
            window.URL.revokeObjectURL(url);
        }, 100);
        
    } catch (error) {
        console.error('Error:', error);
    }
});
        
