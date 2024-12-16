document.addEventListener("DOMContentLoaded", () => {
  fetchFiles(); // Fetch files when the page is loaded
});
const updatePrivacyList = {}
const fileDisplay = document.getElementById("fileDisplay");
const convertButton = document.getElementById("startConvertingButton");
convertButton.addEventListener("click", redirectToConverter);

let files = [];
let selectedFiles = new Set();

// Fetch files from the backend
async function fetchFiles() {
  try {
    fileDisplay.innerHTML = "<p>Loading files...</p>"; // Show loading state
    const response = await fetch("/files");
    if (!response.ok) {
      throw new Error("Failed to fetch files.");
    }
    const data = await response.json();
    files = data.files || []; // Assuming the backend sends { files: [...] }
    displayFiles();
  } catch (error) {
    console.error(error);
    fileDisplay.innerHTML = `<p>Error fetching files: ${error.message}</p>`;
  }
}

// Display files in the list
async function displayFiles() {
  fileDisplay.innerHTML = ""; // Clear existing content

  if (files.length === 0) {
    fileDisplay.innerHTML = "<p>No files available.</p>";
    return;
  }

  files.forEach((file, index) => {
    const listItem = document.createElement("div");
    listItem.classList.add("file-item");

    // Extract file properties
    const { hash: filehash, path: filepath, username, private: isPrivate, 
            file_name: filename, file_type: filetype, file_size: filesize, 
            duration, date } = file;
    const readableFileSize = formatFileSize(filesize);
    
    listItem.innerHTML = `
      <div class="file-checkbox">
        <input type="checkbox" data-index="${index}" class="file-select-checkbox">
      </div>
      <div class="file-info">
        <strong>${filename}</strong> <!-- Display the file name -->
        <span>${readableFileSize}</span>
        <span>${filetype}</span>
        <span>${date}</span>
      </div>
      <div class="file-privacy">
        <label for="privacy-toggle-${index}">Privacy:</label>
        <select id="privacy-toggle-${index}" class="privacy-toggle">
          <option value="public" ${isPrivate ? "" : "selected"}>Public</option>
          <option value="private" ${isPrivate ? "selected" : ""}>Private</option>
        </select>
        
      </div>
      <div class="file-actions">
        <button class="view-button" onclick="viewFile('${filehash}')">View</button>
        <button class="download-button" onclick="downloadFile('${filehash}')">Download</button>
      </div>
    `;

    // Fetch the thumbnail and dynamically create the image element
    fetch(`/thumbnail/${filehash}`)
      .then(response => {
        if (!response.ok) {
          throw new Error("Network response was not ok");
        }
        return response.blob(); // Convert response to Blob
      })
      .then(imageBlob => {
        const imageUrl = URL.createObjectURL(imageBlob); // Create a URL for the blob

        // Create the thumbnail container and image element
        const thumbnailContainer = document.createElement("div");
        thumbnailContainer.classList.add("file-thumbnail");

        const thumbnailImg = document.createElement("img");
        thumbnailImg.src = imageUrl; // Set the image source
        thumbnailImg.alt = "Thumbnail"; // Set alt text
        thumbnailContainer.appendChild(thumbnailImg); // Add image to container

        // Insert the thumbnail container into the list item
        listItem.insertBefore(thumbnailContainer, listItem.querySelector(".file-info"));
      })
      .catch(error => {
        console.error("Error fetching thumbnail:", error);
      });

    // Add event listener for checkbox change
    const checkbox = listItem.querySelector(".file-select-checkbox");
    checkbox.addEventListener("change", (e) => toggleSelection(index, e.target.checked));
    const privacyToggle = listItem.querySelector(`#privacy-toggle-${index}`);
    privacyToggle.addEventListener("change", (e) => updatePrivacy(filehash, e.target.value));
    // Append the list item to the display container
    fileDisplay.appendChild(listItem);
  });
}

function toggleSelection(index, isChecked) {
  const filehash = files[index].hash; 

  if (isChecked) {
    selectedFiles.add(filehash);
  } else {
    selectedFiles.delete(filehash);
  }

  if (selectedFiles.size > 0) {
    convertButton.disabled = false; 
    convertButton.style.display = 'block';
  } else {
    convertButton.disabled = true; 
    convertButton.style.display = 'none';
  }
}

// View file
function viewFile(fileHash) {
  window.location.href = `/file/${fileHash}`;
}

// Download file
function downloadFile(fileHash) {
  window.location.href = `/download/${fileHash}`;
}
document.querySelector(".sort-button").addEventListener("click", () => {
  sortFiles();
});

document.querySelector(".filter-button").addEventListener("click", () => {
  alert("Filter functionality is not yet implemented!");
});

document.querySelector(".search-button").addEventListener("click", () => {
  const searchTerm = prompt("Enter a file name to search:");
  if (searchTerm) {
    searchFiles(searchTerm);
  }
});

// Sort files by name (ascending)
function sortFiles() {
  files.sort((a, b) => a[0].localeCompare(b[0])); // Assuming file[0] contains the file name
  displayFiles();
}

// Search for files by name
function searchFiles(term) {
  const searchResults = files.filter((file) => file[0].toLowerCase().includes(term.toLowerCase()));
  if (searchResults.length > 0) {
    files = searchResults;
    displayFiles();
  } else {
    alert("No files matched your search!");
  }
}

function formatFileSize(bytes) {
  const units = ["bytes", "KB", "MB", "GB", "TB"];
  let unitIndex = 0;

  while (bytes >= 1024 && unitIndex < units.length - 1) {
    bytes /= 1024;
    unitIndex++;
  }

  return `${bytes.toFixed(2)} ${units[unitIndex]}`; 
}
function updatePrivacy(filehash, privacy) {
  if (updatePrivacyList.hasOwnProperty(filehash)) {
    delete updatePrivacyList[filehash];
  } else {
    updatePrivacyList[filehash] = privacy;
  }
}
function savePrivacy() {
  Object.entries(updatePrivacyList).forEach(async ([filehash, privacy]) => {
    try {
      const response = await fetch(`/update-privacy/${filehash}/${privacy}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ privacy: privacy }),
      });

      if (!response.ok) {
        throw new Error("Failed to update privacy.");
      }

      alert(`Privacy of file ${filehash} updated to `);
    } catch (error) {
      console.error(error);
      alert("There was an error updating the file privacy.");
    }
  });
}
function redirectToConverter() {
  if (selectedFiles.size === 0) {
      alert("No files selected! Please select at least one file.");
      return;
  }

  const combinedHashes = Array.from(selectedFiles).join("+");
  const url = `/converter/${combinedHashes}`;
  console.log(`Redirecting to: ${url}`);
  window.location.href = url;
}
