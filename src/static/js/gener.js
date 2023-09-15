document.addEventListener("DOMContentLoaded", function () {
    
    const generationForm = document.getElementById("generation-form");
    const versionCheckboxes = generationForm.querySelectorAll('.version-checkbox');
    const folderCheckboxes = generationForm.querySelectorAll('.folder-checkbox'); 

    const engineUrlInput = document.getElementById("engine_url");

    // Ajoutez le code pour sauvegarder et récupérer la valeur de l'URL du moteur ici
    engineUrlInput.addEventListener("input", function () {
        const engineUrl = engineUrlInput.value;
        localStorage.setItem("engine_url", engineUrl);
    });
    
    // Récupérez la valeur de l'URL du moteur depuis le stockage local au chargement de la page
    const storedEngineUrl = localStorage.getItem("engine_url");
    
    if (storedEngineUrl) {
        engineUrlInput.value = storedEngineUrl;
    }

    function showProgressBar() {
        const popup = document.getElementById('progress-popup');
        popup.style.display = 'block';
    }
    
    function hideProgressBar() {
        const popup = document.getElementById('progress-popup');
        popup.style.display = 'none';
    } 
    
    const folderItems = document.querySelectorAll(".folder-item");
    const imageBubble = document.getElementById("image-bubble");

    folderItems.forEach(folderItem => {
        folderItem.addEventListener("mouseover", function() {
            const folderName = folderItem.dataset.folder;
            fetchAndDisplayImage(folderName, folderItem);
        });
    });

    function fetchAndDisplayImage(folderName, folderItem) {
        fetch('/get_image/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify({ folderName: folderName }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                displayImageInBubble(data.imageURL, folderItem);
            }
        })
        .catch(error => console.error('Erreur', error));
    }

    function displayImageInBubble(imageURL, folderItem) {
        imageBubble.innerHTML = `<img src="${imageURL}" alt="Image du dossier" class="centered-image">`;

        folderItem.addEventListener("mouseout", function() {
            hideImage();
        });

        imageBubble.style.display = "block";
    }

    function hideImage() {
        imageBubble.innerHTML = ''; // Effacer le contenu de la bulle
        imageBubble.style.display = "none";
    }

    generationForm.addEventListener("submit", function (event) {
        event.preventDefault();
    
        const selectedVersions = Array.from(versionCheckboxes).filter(checkbox => checkbox.checked).map(checkbox => checkbox.value);
        const selectedFolders = Array.from(folderCheckboxes).filter(checkbox => checkbox.checked).map(checkbox => checkbox.value);

        if (selectedVersions.length === 0 || selectedFolders.length === 0) {
            hideProgressBar(); // Cacher la fenêtre contextuelle
            alert("Veuillez sélectionner au moins un élément dans chaque liste.");
            return; // Empêche le code suivant d'être exécuté
        }
    
        // Récupérez l'URL du moteur à partir de l'élément engine_url
        const engineUrl = document.getElementById("engine_url").value;
    
        // Vérifiez que l'URL de l'image a au moins un caractère avant de l'ajouter
        if (engineUrl.length > 0) {
            const formData = new FormData();
            showProgressBar(); // Afficher la fenêtre contextuelle
            selectedVersions.forEach(version => {
                formData.append('selected_versions[]', version);  // Note the "[]" in the name
            });
    
            selectedFolders.forEach(folder => {
                formData.append('selected_folders[]', folder);  // Note the "[]" in the name
            });
    
            formData.append('engine_url', engineUrl); // Ajoutez l'URL du moteur ici
    
            fetch('/get_parameters/', {
                
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: formData
            })
            .then(response => response.json())
            .finally(() => {
                // Masquer la barre de progression à la fin de la promesse
                hideProgressBar();
            })
            .then(data => {
                if (data.success) {
                } else {
                    alert(data.message); 
                }
            });
        } else {
            // Gérez le cas où l'URL de l'image est vide ou ne contient que des espaces
            hideProgressBar();
            alert("L'URL du moteur est vide.");
        }
    });

    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});