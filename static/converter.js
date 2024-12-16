const hashList = document.getElementById('hashList');
const fileHashes = getFileHashesFromURL();

function getFileHashesFromURL() {
  // Get the current URL path
  const path = window.location.pathname;

  // Extract the part after "/converter/"
  const prefix = "/converter/";
  if (path.startsWith(prefix)) {
      const combinedFileHashes = path.slice(prefix.length);

      // Split the combined hashes by "+"
      const fileHashes = combinedFileHashes.split("+");
      return fileHashes;
  }

  // Return an empty array if the URL doesn't match
  return [];
}async function handleClick(action) {
  if (action === 'FileType') {
      const response = await fetch(`/filetype/check?combined_filehashes=${fileHashes.join("+")}`);
      const data = await response.json();

      const optionsDiv = document.getElementById('optionsDiv');
      optionsDiv.innerHTML = ''; // Clear previous options

      if (data.all_same) {
          const filetype = data.filetype;

          // Display filetype adjustment option
          const filetypeLabel = document.createElement('p');
          filetypeLabel.textContent = `All files are of type: ${filetype}`;
          optionsDiv.appendChild(filetypeLabel);

          const filetypeInput = document.createElement('input');
          filetypeInput.type = 'text';
          filetypeInput.placeholder = 'New filetype';
          filetypeInput.id = 'newFileType';
          optionsDiv.appendChild(filetypeInput);

          // If the filetype is video, add additional options
          if (filetype === 'video') {
              const parameters = [
                  "videobitrate",
                  "audiobitrate",
                  "videocodec",
                  "audiocodec",
                  "resolution",
                  "framerate"
              ];

              parameters.forEach(param => {
                  const label = document.createElement('label');
                  label.textContent = param;
                  const input = document.createElement('input');
                  input.type = 'text';
                  input.id = param;
                  optionsDiv.appendChild(label);
                  optionsDiv.appendChild(input);
                  optionsDiv.appendChild(document.createElement('br'));
              });
          }

          // Submit button
          const submitButton = document.createElement('button');
          submitButton.textContent = 'Submit';
          submitButton.onclick = () => submitFileTypeOptions();
          optionsDiv.appendChild(submitButton);
      } else {
          alert('Files are of different types, file type adjustment is not possible.');
      }
  }
}

function submitFileTypeOptions() {
  const newFileType = document.getElementById('newFileType').value;
  const videoParams = [
      "videobitrate",
      "audiobitrate",
      "videocodec",
      "audiocodec",
      "resolution",
      "framerate"
  ];

  const parameters = { filetype: newFileType };
  videoParams.forEach(param => {
      const input = document.getElementById(param);
      if (input) parameters[param] = input.value;
  });

  console.log('Submitting options:', parameters);
  // Perform an API request to process these options as needed
}
