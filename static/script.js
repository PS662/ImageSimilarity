// Handle "Search With Image" button
document.getElementById('imageSearchButton').addEventListener('click', async () => {
    document.getElementById('loading').style.display = 'block';

    const fileInput = document.createElement('input');
    fileInput.type = 'file';
    fileInput.onchange = async () => {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

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

// FIXME: Add folder picker
document.getElementById('updateCatalogueButton').addEventListener('click', async () => {
    const folderPath = prompt("Enter the folder path for the catalogue:");
    if (!folderPath) {
        alert("Folder path is required.");
        return;
    }

    const modelId = prompt("Enter the model ID (optional, press Enter to skip):");
    
    const formData = new FormData();
    formData.append("folder_path", folderPath);
    if (modelId) {
        formData.append("model_id", modelId);  // Add model_id if provided
    }

    try {
        const response = await fetch('/upload_catalogue', {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Error: ${response.statusText}`);
        }

        const data = await response.json();

        if (!data.task_id) {
            throw new Error("Task ID is missing from the response.");
        }

        pollTaskStatus(data.task_id);
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
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
                alert('Task Completed!');
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
