document.addEventListener('DOMContentLoaded', async () => {
    await populateModelDropdown();
});

async function populateModelDropdown() {
    const modelLabel = document.createElement('label');
    modelLabel.htmlFor = 'modelDropdown';
    modelLabel.style.fontSize = '16px';
    modelLabel.style.marginRight = '10px';

    const modelDropdown = document.createElement('select');
    modelDropdown.id = 'modelDropdown';
    modelDropdown.style.marginLeft = '10px';

    try {
        const response = await fetch('/config/model_config.json');
        if (!response.ok) {
            throw new Error(`Error fetching model config: ${response.statusText}`);
        }
        const modelConfig = await response.json();

        modelConfig.forEach(model => {
            const option = document.createElement('option');
            option.value = model.model_id;
            option.textContent = model.model_id;
            modelDropdown.appendChild(option);
        });
    } catch (error) {
        alert(`Failed to load model IDs: ${error.message}`);
    }

    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.marginBottom = '20px'; 

    container.appendChild(modelLabel);
    container.appendChild(modelDropdown);

    const header = document.querySelector('h1');
    document.body.insertBefore(container, header);
}

document.getElementById('updateCatalogueButton').addEventListener('click', async () => {
    const folderInput = document.createElement('input');
    folderInput.type = 'file';
    folderInput.webkitdirectory = true; // Enable folder selection
    folderInput.directory = true;

    folderInput.onchange = async () => {
        const files = folderInput.files;
        if (!files.length) {
            alert("Please select a folder.");
            return;
        }

        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }
        // FIXME: Fix alignment
        const modelId = document.getElementById('modelDropdown').value; // Get selected model
        if (modelId) {
            formData.append('model_id', modelId);
        }

        try {
            const response = await fetch('/upload_catalogue', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            alert("Catalogue uploaded successfully!");
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    };

    folderInput.click();
});

// Handle "Search With Image" button
document.getElementById('imageSearchButton').addEventListener('click', async () => {
    document.getElementById('loading').style.display = 'block';

    const fileInput = document.createElement('input');
    fileInput.type = 'file';

    fileInput.onchange = async () => {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        const modelId = document.getElementById('modelDropdown').value; // Get selected model
        if (modelId) {
            formData.append('model_id', modelId);
        }

        try {
            const response = await fetch('/search_with_image', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const data = await response.json();

            if (!data.task_id) {
                throw new Error('Task ID is missing from the response.');
            }

            pollTaskStatus(data.task_id);
        } catch (error) {
            document.getElementById('loading').style.display = 'none';
            alert(`Error: ${error.message}`);
        }
    };

    fileInput.click();
});

// Poll task status
function pollTaskStatus(taskId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`/poll_task_status/${taskId}`);
            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }

            const data = await response.json();

            if (data.status === 'SUCCESS') {
                clearInterval(interval);
                document.getElementById('loading').style.display = 'none';

                if (!data.result || data.result.error) {
                    // Alert if there's an error or no valid results
                    alert(data.result.error || "No valid results returned.");
                    displayNoResults(data.result.error || "No valid results returned.");
                    return;
                }

                if (!Array.isArray(data.result)) {
                    // Alert if the result is not an array
                    alert("Unexpected result format received. Please try again.");
                    displayNoResults("Unexpected result format received.");
                    return;
                }

                // If all checks pass, display the results
                displaySearchResults(data.result);

            } else if (data.status === 'FAILURE') {
                clearInterval(interval);
                document.getElementById('loading').style.display = 'none';
                alert('Task Failed.');
            } else {
                document.getElementById('loading').innerText = `Status: ${data.status}`;
            }
        } catch (error) {
            clearInterval(interval);
            document.getElementById('loading').style.display = 'none';
            alert(`Error: ${error.message}`);
        }
    }, 1000);
}

// Display search results
function displaySearchResults(results) {
    const container = document.createElement('div');
    container.className = 'result-grid';

    results.forEach(result => {
        const resultDiv = document.createElement('div');
        resultDiv.className = 'result-item';

        const img = document.createElement('img');

        if (result.image_uri) {
            img.src = result.image_uri;
            img.alt = 'Search Result';
        } else {
            img.src = '/static/placeholder.png'; 
            img.alt = 'No image available';
        }

        img.style.width = '100px';
        img.style.height = '100px';

        const similarityText = document.createElement('p');
        similarityText.textContent = `Similarity: ${((1 - result.distance) * 100).toFixed(2)}%`;

        resultDiv.appendChild(img);
        resultDiv.appendChild(similarityText);
        container.appendChild(resultDiv);
    });

    const existingGrid = document.querySelector('.result-grid');
    if (existingGrid) {
        existingGrid.replaceWith(container);
    } else {
        document.body.appendChild(container);
    }
}

// Handle no results case
function displayNoResults(errorMessage) {
    const container = document.createElement('div');
    container.className = 'no-results';

    const message = document.createElement('p');
    message.textContent = `No results found: ${errorMessage}`;
    message.style.color = 'red';

    const existingGrid = document.querySelector('.result-grid') || document.querySelector('.no-results');
    if (existingGrid) {
        existingGrid.replaceWith(container);
    } else {
        document.body.appendChild(container);
    }
}

