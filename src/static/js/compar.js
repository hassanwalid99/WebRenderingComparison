document.addEventListener('DOMContentLoaded', function () {
    const addButton = document.getElementById('add_selection');
    const viewAllImagesButton = document.getElementById('view-all-images');
    const selectionsContainer = document.getElementById('selections-container');
    const selectedImagesList = document.querySelector('.selected-images-list');
    const selectedImagesNotDisplayedList = document.querySelector('.selected-images-not-displayed-list');

    const initialSelection = document.querySelector('.selection-group');
    const newSelectionGroup = initialSelection.cloneNode(true);
    createSelection(newSelectionGroup);

    function updateDestinationSelect(sourceSelect, destinationSelect) {
        const selectedSource = sourceSelect.value;
        destinationSelect.innerHTML = ''; // Réinitialiser la liste de destination

        if (selectedSource) {
            fetch(`/get_subfolders/?source=${selectedSource}`)
                .then(response => response.json())
                .then(data => {
                    data.forEach(folder => {
                        const option = document.createElement('option');
                        option.value = folder;
                        option.textContent = folder;
                        destinationSelect.appendChild(option);
                    });

                    // Mettre à jour les listes d'images
                    updateSelectedImagesLists();
                })
                .catch(error => console.error('Error fetching subfolders:', error));
        }
    }

    function updateSelectedImagesLists() {
        selectedImagesList.innerHTML = ''; // Réinitialiser la liste
        selectedImagesNotDisplayedList.innerHTML = ''; // Réinitialiser la liste
    
        const selectionGroups = document.querySelectorAll('.selection-group');
        const selectedFolders = [];
        const selectedSubfolders = [];
    
        selectionGroups.forEach(function (group) {
            const sourceSelect = group.querySelector('.source_select');
            const destinationSelect = group.querySelector('.destination_select');
    
            const selectedFolder = sourceSelect.value;
            const selectedSubfolder = destinationSelect.value;
    
            if (selectedFolder && selectedSubfolder) {
                selectedFolders.push(selectedFolder);
                selectedSubfolders.push(selectedSubfolder);
            }
        });
    
        // Envoyer la liste des dossiers et sous-dossiers sélectionnés dans la requête AJAX
        const selectedFoldersQueryParam = selectedFolders.map(folder => `selected_folder=${folder}`).join('&');
        const selectedSubfoldersQueryParam = selectedSubfolders.map(subfolder => `selected_subfolder=${subfolder}`).join('&');
        
        fetch(`/check_image_presence/?${selectedFoldersQueryParam}&${selectedSubfoldersQueryParam}`)
            .then(response => response.json())
            .then(data => {
                data.images_to_display.forEach(imageName => {
                    // Créer un élément li pour afficher le nom de l'image
                    const li = document.createElement('li');
                    li.textContent = imageName;
    
                    selectedImagesList.appendChild(li);
                });
    
                data.images_not_displayed.forEach(imageName => {
                    // Créer un élément li pour afficher le nom de l'image non affichée
                    const li = document.createElement('li');
                    li.textContent = imageName;
                    const missingInfo = data.image_missing_info[imageName];  // Récupérer les dossiers manquants
                    if (missingInfo) {
                        li.title = `Dossiers où l'image manque : \n- ${missingInfo.join('\n- ')}`;
                    }
    
                    selectedImagesNotDisplayedList.appendChild(li);
                });
            })
            .catch(error => console.error('Error fetching image presence:', error));
    }
    

    function createSelection(selectionGroup) {
        selectionsContainer.appendChild(selectionGroup);

        // Mettre à jour les éléments dans la nouvelle sélection
        const newSourceSelect = selectionGroup.querySelector('.source_select');
        const newDestinationSelect = selectionGroup.querySelector('.destination_select');

        // Réinitialiser la deuxième liste déroulante à chaque création
        newDestinationSelect.innerHTML = '<option value="" disabled selected>Choisir</option>';

        newSourceSelect.addEventListener('change', function () {
            updateDestinationSelect(newSourceSelect, newDestinationSelect);
        });

        newDestinationSelect.addEventListener('change', function () {
            updateSelectedImagesLists();
        });
        // Ajoutez la paire de sélection au conteneur principal
        selectionsContainer.appendChild(selectionGroup);

        // Si le nombre total de paires est supérieur ou égal à 3, ajoutez le bouton "X"
        if (document.querySelectorAll('.selection-group').length >= 3) {
            const deleteButton = document.createElement('button');
            deleteButton.textContent = 'X';
            deleteButton.addEventListener('click', function () {
                // Supprimez le groupe de sélection lorsqu'on clique sur le bouton "X"
                selectionsContainer.removeChild(selectionGroup);
                // Mettez à jour les listes d'images après la suppression
                updateSelectedImagesLists();
            });

            // Ajoutez le bouton "X" à côté de la paire
            selectionGroup.appendChild(deleteButton);
        }
    }

    addButton.addEventListener('click', function () {
        const initialSelectionGroup = document.querySelector('.selection-group');
        const newSelectionGroup = initialSelectionGroup.cloneNode(true);
        createSelection(newSelectionGroup);
    });

    viewAllImagesButton.addEventListener('click', function () {
        const selectionGroups = document.querySelectorAll('.selection-group');
        const selectedOptions = [];
    
        // Vérifiez si toutes les paires de sélection sont remplies
        const allPairsFilled = Array.from(selectionGroups).every(function (group) {
            const sourceSelect = group.querySelector('.source_select');
            const destinationSelect = group.querySelector('.destination_select');
            return sourceSelect.value && destinationSelect.value;
        });
    
        if (!allPairsFilled) {
            alert("Veuillez remplir toutes les paires de sélection.");
            return; // Ne continuez pas si au moins une paire de sélection n'est pas remplie
        }
    
        // Vérifiez si au moins une case à cocher est sélectionnée dans les options
        const checkboxes_test = document.querySelectorAll('input[name="option"]:checked');
        if (checkboxes_test.length === 0) {
            alert("Veuillez sélectionner au moins une option.");
            return; // Ne continuez pas si aucune option n'est sélectionnée
        }
    
        // Vérifiez si la liste des "Images Affichées" est vide
        const selectedImagesList = document.querySelector('.selected-images-list');
        if (selectedImagesList.children.length === 0) {
            alert("Comparaison impossible ! Veuillez voir la liste des Images Non Affichées");
            return; // Ne continuez pas si la liste est vide
        }

        // Récupérer les cases à cocher sélectionnées
        const checkboxes = document.querySelectorAll('input[name="option"]:checked');
        checkboxes.forEach(function (checkbox) {
            selectedOptions.push(checkbox.value);
        });
    
        // Si toutes les vérifications passent, continuez avec la comparaison
        const queryStringParts = Array.from(selectionGroups).map(function (group) {
            const sourceSelect = group.querySelector('.source_select');
            const destinationSelect = group.querySelector('.destination_select');
            return `selected_folder=${sourceSelect.value}&selected_subfolder=${destinationSelect.value}`;
        });
    
        const optionsQueryString = `selected_options=${selectedOptions.join(',')}`;
        const queryString = queryStringParts.join('&') + '&' + optionsQueryString;
        const url = `/view_all_images/?${queryString}`;
        window.open(url, '_blank');
    });
    

    const initialSelectionGroup = document.querySelector('.selection-group');
    createSelection(initialSelectionGroup);;
});