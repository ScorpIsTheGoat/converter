document.addEventListener("DOMContentLoaded", () => {
  fetchFiles(); 
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
    document.getElementById("uploadedFiles").innerHTML = "<p>Loading files...</p>";
    document.getElementById("convertedFiles").innerHTML = "<p>Loading files...</p>";

    const response = await fetch("/files");
    if (!response.ok) {
      throw new Error("Failed to fetch files.");
    }

    const data = await response.json();
    const [uploadedFiles, convertedFiles] = data.files || [[], []];

    displayFiles(uploadedFiles, "uploadedFiles");
    displayFiles(convertedFiles, "convertedFiles");
  } catch (error) {
    console.error(error);
    document.getElementById("uploadedFiles").innerHTML = `<p>Error: ${error.message}</p>`;
    document.getElementById("convertedFiles").innerHTML = `<p>Error: ${error.message}</p>`;
  }
}

function displayFiles(files, containerId) {
  const container = document.getElementById(containerId);
  container.innerHTML = ""; // Clear previous content

  if (files.length === 0) {
    container.innerHTML = "<p>No files available.</p>";
    return;
  }

  files.forEach((file) => {
    const listItem = document.createElement("div");
    listItem.classList.add("file-item");

    const { hash: filehash, file_name: filename, file_size: filesize, file_type: filetype, private: privacy } = file;

    listItem.innerHTML = `
      <div class="file-thumbnail">
        <img src="/thumbnail/${filehash}" alt="Thumbnail for ${filename}" onerror="this.src='/static/default-thumbnail.png';" />
      </div>
      <div class="file-info">
        <strong class="file-name">${filename}</strong>
        <span>${formatFileSize(filesize)}</span>
        <span>${filetype}</span>
      </div>
      <div class="file-actions">
        <button class="delete-button" id="delete-${filehash}">Delete</button>
        <select class="privacy-select" id="privacy-${filehash}">
          <option value="public" ${privacy === 0 ? 'selected' : ''}>Public</option>
          <option value="private" ${privacy === 1 ? 'selected' : ''}>Private</option>
        </select>
      </div>
      <div class="file-checkbox">
        <input type="checkbox" id="checkbox-${filehash}" />
      </div>
    `;

    const filenameElement = listItem.querySelector(".file-name");
    filenameElement.addEventListener("click", () => {
      window.location.href = `/file/${filehash}`;
    });

    const deleteButton = listItem.querySelector(`#delete-${filehash}`);
    deleteButton.addEventListener("click", () => {
      deleteFile(filehash);
    });

    const privacySelect = listItem.querySelector(`#privacy-${filehash}`);
    privacySelect.addEventListener("change", (event) => {
      updatePrivacy(filehash, event.target.value);
    });

    const checkbox = listItem.querySelector(`#checkbox-${filehash}`);
    checkbox.addEventListener("change", (event) => {
      toggleSelection(filehash, event.target.checked);
    });

    container.appendChild(listItem);
  });
}


function toggleSelection(filehash, isChecked) {
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


function sortFiles() {
  files.sort((a, b) => a[0].localeCompare(b[0]));
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
async function deleteFile(filehash) {
  if (confirm("Are you sure you want to delete this file?")) {
    try {
      const response = await fetch(`/delete/${filehash}`, {
        method: "GET",
      });

      if (!response.ok) {
        throw new Error("Failed to delete file.");
      }

      // Refresh the file list after deletion
      fetchFiles();
    } catch (error) {
      console.error(error);
      alert("There was an error deleting the file.");
    }
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
