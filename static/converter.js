const hashList = document.getElementById('hashList');
const fileHashes = getFileHashesFromURL();
const buttonsContainer = document.querySelector(".button-container")
const titleText = document.getElementById('title-text');
const converterText = document.getElementById('converter-text');
const submitButton = document.getElementById('submit-button')
let fileCounter = 1;
let currentStep = 1;
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
    return [];
}

async function handleClick(action) {
    buttonsContainer.style.display = "none";
    
    if (action === 'FileType') {
        const response = await fetch(`/filetype/check/${fileHashes}`);
        const data = await response.json();
        if (data.all_same) {
            titleText.innerText = "Converter";
            converterText.innerText = "Convert your files to a different format";
            optionsDiv.style.gridTemplateRows = `1fr 10fr`;
            optionsDiv.innerHTML = `
            <div id="action-text"></div>
            <div id="container">
                <div id="files-cell">
                    <div id="files"></div>
                    <div id="convert-cell">
                        <div id="add-files-button-cell">
                            <button id="add-files-button">+ Add More Files</button>
                        </div>
                        <div id="convert-button-cell">
                            <button id="convert-button">Convert</button>
                        </div>
                    </div>
                </div>
            </div>
            `
            
            for (const fileHash of fileHashes) {
                const responseFileInformation = await fetch(`/file-information/${fileHash}`)
                const fileInformation = await responseFileInformation.json();
                const properties = fileInformation['properties']
                const fileName = properties['file_name'];
                const fileExtension = properties['file_type'];
                addRowToGrid(fileName, fileExtension)
            }
            document.getElementById('convert-button').addEventListener('click', function() {
                submitFileTypeOptions(fileHashes);
            });
        } else {
            alert('Files are of different types, file type adjustment is not possible.');
        }
    }
    else if (action === "Subtitler"){
        titleText.innerText = "Subtitler";
        converterText.innerText = "Choose your desired service"
        optionsDiv.innerHTML = `
        <div id="optionsDiv">
            <div id="step1">
                <button id="transcribe-btn" onclick="chooseTask('transcribe')">Transcribe</button>
                <button id="translate-btn" onclick="chooseTask('translate')">Translate to English</button>
            </div>

            <div id="step2" class="hidden">
                <h2>Select Video Language:</h2>
                <select id="language">
                    <option value="auto">Auto Detect</option>
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                </select>
            </div>

            <div id="step3" class="hidden">
                <button id="tiny-btn" onclick="chooseModel('tiny')">Tiny</button>
                <button id="small-btn" onclick="chooseModel('small')">Small</button>
                <button id="medium-btn" onclick="chooseModel('medium')">Medium</button>
                <button id="large-btn" onclick="chooseModel('large')">Large</button>
            </div>

        </div>

        <div id="output" class="hidden">
            <h2>Subtitles Generated:</h2>
            <pre id="subtitles"></pre>
        </div>
      `;
        const button = document.createElement("button");
        button.id = "next-button";
        button.textContent = "Next";
        button.addEventListener("click", nextStep);        
        document.body.appendChild(button);
        const actionButtons = document.querySelectorAll('#action-options button');
        const modelButtons = document.querySelectorAll('#model-options button');
    }
    else if (action === "ColorGrader"){
        titleText.innerText = "ColorGrader";
        converterText.innerText = "Choose preset"
        submitButton.classList.remove("hidden")
        optionsDiv.innerHTML = `
        <select id="preset">
          <option value="cinematic">Cinematic</option>
          <option value="black-and-white">Black and White</option>
          <option value="colorful">Colorful</option>
        </select>
        
      `;
    }
    else if (action === "Upscaler"){
        optionsDiv.innerHTML = `
        <h2>Upscaler Options</h2>
        <label for="resolution">New Resolution:</label>
        <input type="text" id="resolution" placeholder="e.g., 1920x1080">
        <button onclick="submitOptions()">Submit</button>
      `;
    }
}
function nextStep() {
    document.getElementById(`step${currentStep}`).classList.add("hidden");
    currentStep++;
    if (document.getElementById(`step${currentStep}`)) {
        document.getElementById(`step${currentStep}`).classList.remove("hidden");
    } 
    if (currentStep === 3) {
        document.getElementById("submit-button").classList.remove("hidden");
        document.getElementById("next-button").classList.add("hidden");
    } 
}
function showNextButton() {
    document.getElementById("next-button").classList.remove("hidden");
}

function hideNextButton() {
    document.getElementById("next-button").classList.add("hidden");
}
async function submitFileTypeOptions(fileHashes) {
    let counter = 1;
    for (const fileHash of fileHashes) {
        const filenameText = document.getElementById(`filename-${counter}`).innerText;
        const parts = filenameText.split('.');
        const fileExtension = parts[parts.length - 1]; // Get the last element which is the extension
        const fileType = classifyFileType(fileExtension);
        const newFileExtension = document.getElementById(`filetype-${counter}`).value;
        counter++;

        let Params = [];
        if (fileType === "video") {
            Params = ["videobitrate", "audiobitrate", "videocodec", "audiocodec", "resolution", "framerate"];
        } else if (fileType === "image") {
            Params = ["resolution"];
        }

        // Build the parameters object
        const parameters = { filetype: newFileExtension };
        Params.forEach(param => {
            const input = document.getElementById(param);
            if (input) parameters[param] = input.value;
        });

        // Build URL with parameters
        const baseurl = buildURLWithParameters("/convert", parameters);
        let filehashurl = `${baseurl}/${fileHash}`;

        try {
            // Make a GET request to check conversion status
            const response = await fetch(filehashurl, { method: "GET" });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            console.log("Response data:", data);

            // Find the file container in the grid
            const fileContainer = document.getElementById(`file-${counter - 1}`);

            if (data.msg === "has already been converted") {
                console.log("This file has already been converted.");

                // Create a message element
                const messageElement = document.createElement("p");
                messageElement.textContent = "Already converted";
                messageElement.style.color = "red"; // Make it visually distinct
                messageElement.style.fontWeight = "bold";

                // Append the message to the file container
                fileContainer.appendChild(messageElement);
            } else if (data.msg) {
                const fileLink = `/file/${data.msg}`;
                console.log(`File converted successfully! Access it here: ${fileLink}`);

                // Create a success message with a download link
                const messageElement = document.createElement("p");
                messageElement.innerHTML = `Converted! <a href="${fileLink}" target="_blank">Download here</a>`;
                messageElement.style.color = "green"; 
                messageElement.style.fontWeight = "bold";

                // Append the message to the file container
                fileContainer.appendChild(messageElement);
            }
        } catch (error) {
            console.error("Error making the fetch request:", error);
        }
    }
}
async function submitSubtitlerOptions(){
    optionsDiv.innerHTML = "<h1>Is Converting</h1>";
    const languageSelect = document.getElementById('language');
    const language = languageSelect.value;
    Params = [
        "action",
        "language",
        "model"
        
    ];
    const parameters = {};
    
    parameters["action"] = selectedAction
    parameters["language"] = language;
    parameters["model"] = selectedModel
    // Build URL with parameters
    const baseurl = buildURLWithParameters("/stt", parameters);

    // Append file hashes to the URL
    let filehashurl = baseurl;
    fileHashes.forEach((hash, index) => {
        if (index === 0) {
            filehashurl += `/${hash}`;
        } else {
            filehashurl += `+${hash}`;
        }
    });
    try {
        // Make a GET request to the constructed URL
        const response = await fetch(filehashurl, {
            method: "GET",
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        console.log("Response data:", data);
        

        // Handle the data as needed
    } catch (error) {
        console.error("Error making the fetch request:", error);
    }
}
function getFocusedButtonById(id) {
    const focusedButton = document.querySelector(`#${id} button:focus`);
    return focusedButton ? focusedButton.id : null;
  }


function buildURLWithParameters(baseURL, parameters) {
    const options = [];

    if (parameters.videobitrate) {
        options.push(`vb-${parameters.videobitrate}`);
    }
    if (parameters.audiobitrate) {
        options.push(`ab-${parameters.audiobitrate}`);
    }
    if (parameters.videocodec) {
        options.push(`vc-${parameters.videocodec}`);
    }
    if (parameters.audiocodec) {
        options.push(`ac-${parameters.audiocodec}`);
    }
    if (parameters.resolution) {
        options.push(`res-${parameters.resolution}`);
    }
    if (parameters.framerate) {
        options.push(`fps-${parameters.framerate}`);
    }
    if (parameters.filetype) {
        options.push(parameters.filetype);
    }
    if (parameters.language) {
        options.push(`lang-${parameters.language}`);
    }
    if (parameters.model) {
        options.push(`model-${parameters.model}`);
    }
    if (parameters.action) {
        options.push(`${parameters.action}`);
    }

    const queryString = options.join("+");
    return `${baseURL}/${queryString}`;
}

function addRowToGrid(filename, fileExtension) {
    
    const gridContainer = document.getElementById('files');
    gridContainer.style.gridTemplateRows = `repeat(${fileCounter}, 2fr)`;   
    gridContainer.innerHTML += `
        <div id="file-${fileCounter}" class="file">
            <div id="file-icon-cell-${fileCounter}" class="file-icon-cell"></div>
            <div id="filename-cell-${fileCounter}" class="filename-cell">
                <div id="filename-${fileCounter}" class="filename">${filename}.${fileExtension}</div>
            </div>
            <div id="filetype-cell-${fileCounter}" class="filetype-cell"></div>
            <div id="settings-button-cell-${fileCounter}" class="settings-button-cell">
                <button id="settings-button-${fileCounter}" class="settings-button">
                    <img class="settings-image" src="../static/images/settings.svg" alt="Settings Icon">
                </button>
            </div>
        </div>
    `;
    fileType = classifyFileType(fileExtension)
    const fileIconDiv = document.getElementById(`file-icon-cell-${fileCounter}`);
    const fileIconImg = document.createElement('img');
    fileIconImg.className = 'file-icon'
    fileIconImg.id = `file-icon-${fileCounter}`
    if (fileType == "video"){
        fileIconImg.src = '../static/images/videofile.svg'; // Replace with the actual path to the file icon
        fileIconImg.alt = 'Video File';
    }
    else if (fileType == "image"){
        fileIconImg.src = '../static/images/imagefile.svg'
        fileIconImg.alt = 'Image File'
    }
    else if (fileType == "text"){
        fileIconImg.src = '../static/images/textfile.svg'
        fileIconImg.alt = 'Text File'
    }
    else if (fileType == "audio"){
        fileIconImg.src = '../static/images/audiofile.svg'
        fileIconImg.alt = 'Audio File'
    }
    fileIconDiv.appendChild(fileIconImg);
    //adds the filename 
    
    const filetypeCell = document.getElementById(`filetype-cell-${fileCounter}`);
    const filetypeSelect = document.createElement('select');
    filetypeSelect.id = `filetype-${fileCounter}`;

    if (fileType == "video"){
        options = ['mp4', 'avi', 'mkv', 'mov', 'hevc', 'mpg'];
        
    }
    else if (fileType == "image"){
        options = ['jpg', 'png', 'svg', 'gif', 'raw', 'avif', 'webp']
    }
    else if (fileType == "text"){
        options = ['doc', 'docx', 'md', 'txt', 'pdf']
    }
    else if (fileType == "audio"){
        options = ['mp3', 'wav', 'm4a', 'aiff', 'ogg']
    }
    options.forEach((option) => {
        const optElement = document.createElement('option');
        optElement.value = option.toLowerCase();
        optElement.textContent = option;
        filetypeSelect.appendChild(optElement);
    });
    filetypeCell.appendChild(filetypeSelect);
    //adds the settings button
    fileCounter ++
    

}


function classifyFileType(fileType) {
    const categories = {
        video: ["mp4", "avi", "mov", "mkv", "flv", "wmv"],
        image: ["jpg", "jpeg", "png", "gif", "bmp", "svg", "webp"],
        text: ["txt", "md", "doc", "docx", "pdf", "rtf"],
        audio: ["mp3", "wav", "aac", "flac", "ogg", "m4a"],
        archive: ["zip", "rar", "7z", "tar", "gz"],
        code: ["js", "html", "css", "py", "java", "c", "cpp", "ts"]
    };
    const normalizedType = fileType.toLowerCase();
    for (const [category, extensions] of Object.entries(categories)) {
        if (extensions.includes(normalizedType)) {
            return category;
        }
    }
    return "unknown";
}

function chooseTask(task) {
    // Get all buttons inside #step1
    const buttons = document.querySelectorAll("#step1 button");
    selectedAction = task
    // Reset all buttons to their default color
    buttons.forEach(button => {
        button.style.backgroundColor = "#007BFF"; // Default blue
    });

    // Change the background color of the selected button
    const selectedButton = document.getElementById(task + "-btn");
    selectedButton.style.backgroundColor = "#0056b3"; // Darker blue
}

function chooseModel(model) {
    // Get all buttons inside #step3
    const buttons = document.querySelectorAll("#step3 button");
    selectedModel = model
    // Reset all buttons to their default color
    buttons.forEach(button => {
        button.style.backgroundColor = "#007BFF"; // Default blue
    });

    // Change the background color of the selected button
    const selectedButton = document.getElementById(model + "-btn");
    selectedButton.style.backgroundColor = "#0056b3"; // Darker blue
}

