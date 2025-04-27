document.getElementById('fileInput').addEventListener('change', function (e) {
    const uploadButton = document.getElementById('uploadButton');  // Get the upload button
    const fileListContainer = document.getElementById('fileList');
    const existingFiles = fileListContainer.children;

    const files = e.target.files;
    if (files.length > 0) {
        // Show the upload button if files are selected
        uploadButton.style.display = 'flex'; // Show the upload button

        // Iterate over the selected files and add new ones
        for (let i = 0; i < files.length; i++) {
            const file = files[i];

            // Check if the file is already in the list (based on filename)
            let alreadyAdded = false;
            for (let j = 0; j < existingFiles.length; j++) {
                if (existingFiles[j].querySelector('.file-info').textContent.includes(file.name)) {
                    alreadyAdded = true;
                    break;
                }
            }

            // If the file is not already added, add it to the list
            if (!alreadyAdded) {
                const fileDiv = document.createElement('div');
                fileDiv.classList.add('file-item');

                // Determine the appropriate file type icon
                const fileIcon = document.createElement('img');
                fileIcon.classList.add('file-icon');
                fileIcon.src = getFileTypeIcon(file);  // Get the file type icon based on file extension
                fileIcon.alt = file.type;

                // File Information (limit to 25 characters)
                const fileInfo = document.createElement('span');
                fileInfo.classList.add('file-info');
                fileInfo.textContent = `${truncateFilename(file.name)} (${formatFileSize(file.size)})`;

                // Add the icon and file info to the file div
                fileDiv.appendChild(fileIcon);
                fileDiv.appendChild(fileInfo);

                // Red X SVG Icon for deletion
                const deleteButton = document.createElement('button');
                deleteButton.classList.add('delete-btn');  // Add delete button class

                // Red X SVG Icon
                const deleteIcon = document.createElement('img');
                deleteIcon.src = '../static/images/red_x.svg';  // Path to red_x.svg
                deleteIcon.alt = 'Delete';
                deleteIcon.classList.add('delete-icon');  // Add styling class for the icon

                deleteButton.appendChild(deleteIcon);
                deleteButton.addEventListener('click', function () {
                    removeFile(file, fileDiv); // Pass fileDiv to remove the file visually
                });

                fileDiv.appendChild(deleteButton);
                fileListContainer.appendChild(fileDiv);
            }
        }
    } else {
        // Hide the upload button if no files are selected
        uploadButton.style.display = 'none'; // Hide the upload button
    }
});

// Function to truncate filenames to a max length of 25 characters
function truncateFilename(filename) {
    const maxLength = 25;
    const extensionIndex = filename.lastIndexOf('.'); // Find the last dot (file extension)

    // If there's no extension or the filename is already within the limit, return it as is
    if (extensionIndex === -1 || filename.length <= maxLength) {
        return filename;
    }

    // Calculate the length of the extension (including the dot)
    const extensionLength = filename.length - extensionIndex;

    // If the extension itself is longer than the max length, return the full filename
    if (extensionLength > maxLength) {
        return filename;
    }

    // Calculate the remaining length for the filename (excluding the extension)
    const remainingLength = maxLength - extensionLength;

    // Truncate the filename part and add ellipsis
    const truncatedName = filename.substring(0, remainingLength) + '...';

    // Combine the truncated name and the full extension
    return truncatedName + filename.substring(extensionIndex);
}


// Helper function to get the file type icon based on the file extension
function getFileTypeIcon(file) {
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    const iconMap = {
        'txt': '../static/images/textfile.svg',
        'docx': '../static/images/textfile.svg',
        'pdf': '../static/images/textfile.svg',  // If you want to consider PDFs as text
        'mp3': '../static/images/audiofile.svg',
        'wav': '../static/images/audiofile.svg',
        'ogg': '../static/images/audiofile.svg',
        'flac': '../static/images/audiofile.svg',
        'mp4': '../static/images/videofile.svg',
        'avi': '../static/images/videofile.svg',
        'jpg': '../static/images/imagefile.svg',
        'jpeg': '../static/images/imagefile.svg',
        'png': '../static/images/imagefile.svg',
        'gif': '../static/images/imagefile.svg',
    };

    return iconMap[fileExtension] || '../static/images/file.svg';  // Default to file.svg for unknown types
}

// Helper function to format file size in the highest possible value (KB, MB, GB)
function formatFileSize(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    else if (bytes < 1048576) return `${(bytes / 1024).toFixed(2)} KB`;
    else if (bytes < 1073741824) return `${(bytes / 1048576).toFixed(2)} MB`;
    else return `${(bytes / 1073741824).toFixed(2)} GB`;
}


document.getElementById('uploadForm').addEventListener('submit', async function (e) {
    e.preventDefault();
    const statusElement = document.getElementById('status');
    statusElement.textContent = "Uploading...";

    const fileInput = document.getElementById('fileInput');
    const files = fileInput.files;

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
            statusElement.textContent = 'Upload successful!';
            const lineBreak = document.createElement('br');
            const myFilesButton = document.createElement('button');
            myFilesButton.textContent = 'See Your Uploaded Files';
            myFilesButton.classList.add('my-files-btn'); 
            myFilesButton.addEventListener('click', function () {
                window.location.href = '/my-files';
            });
            statusElement.appendChild(lineBreak);
            statusElement.appendChild(myFilesButton);
        } else {
            statusElement.textContent = 'Upload failed.';
        }
    } catch (error) {
        console.error('Error uploading files:', error);
        statusElement.textContent = 'An error occurred.';
    }
});

function removeFile(fileToRemove, fileDiv) {
    // Find the file input
    const fileInput = document.getElementById('fileInput');
    const files = Array.from(fileInput.files);  // Convert FileList to array for easier manipulation

    // Remove the file from the array
    const updatedFiles = files.filter(file => file !== fileToRemove);
    
    // Create a new DataTransfer object to manage the updated list of files
    const dataTransfer = new DataTransfer();
    updatedFiles.forEach(file => dataTransfer.items.add(file)); // Add remaining files to DataTransfer

    // Update the file input with the new file list
    fileInput.files = dataTransfer.files;

    // Remove the visual representation of the file from the list
    fileDiv.remove(); // This removes the file item from the file list container

    // If no files remain, hide the upload button
    if (updatedFiles.length === 0) {
        document.getElementById('uploadButton').style.display = 'none';
    }
}
