function showTabContent(tabIndex) {
    localStorage.setItem('activeTabIndex', tabIndex);
    // Masquer tous les contenus d'onglets
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });

    // Afficher le contenu de l'onglet sélectionné
    const selectedTabContent = document.getElementById('tab-content-' + tabIndex);
    selectedTabContent.classList.add('active');


    // Mettre à jour les onglets sélectionnés
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.classList.remove('selected');
    });
    const selectedTab = document.querySelector('.tab:nth-child(' + tabIndex + ')');
    selectedTab.classList.add('selected');
}


function addRow(tabl) {
    var table = document.getElementById(tabl);
    var row = table.insertRow();
    var cell1 = row.insertCell(0);
    var cell2 = row.insertCell(1);
    var cell3 = row.insertCell(2);
    var cell4 = row.insertCell(3);
    cell1.innerHTML = '<input type="text" placeholder="Type">';
    cell2.innerHTML = '<input type="text" placeholder="Parametre">';
    cell3.innerHTML = '<input type="text" placeholder="Valeur">';
    cell4.innerHTML = '<button class="delete-row" onclick="deleteRow(this)">X</button>';  
}

function deleteRow(button) {
    var row = button.parentNode.parentNode; // Obtient la ligne parente du bouton
    row.parentNode.removeChild(row); // Supprime la ligne de la table
}

function sendDataToBackend() {
    const nameConfig = document.getElementById('name_config').value;
    const rows = document.querySelectorAll('#config-table tbody tr');
    const parameters = [];

    rows.forEach(row => {
        const inputs = row.querySelectorAll('input');
        const param = {
            'Type': inputs[0].value,
            'Parametre': inputs[1].value,
            'Valeur': inputs[2].value
        };
        parameters.push(param);
    });

    if (!nameConfig || parameters.some(param => !param.Type || !param.Parametre || !param.Valeur)) {
        alert('Veuillez remplir tous les champs.');
        return; // Ne pas envoyer les données si les champs sont vides
    }

    if (parameters.some(param => !["string", "bool", "float", "integer"].includes(param.Type))) {
        alert('Veuillez entrer un type valide (string, bool, float, integer)');
        return;
    }

    // Création de l'objet FormData pour envoyer les données
    const formData = new FormData();
    formData.append('name_config', nameConfig);
    formData.append('parameters', JSON.stringify(parameters));

    fetch('/save_configuration/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            location.reload(); 
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'envoi des données:', error);
    });
}
  
function sendDataToBackend2() {
    const selectedConfig = document.getElementById('name_select').value;
    const rows = document.querySelectorAll('#config-table2 tbody tr');
    const parameters = [];

    rows.forEach(row => {
        const inputs = row.querySelectorAll('input');
        const param = {
            'Type': inputs[0].value,
            'Parametre': inputs[1].value,
            'Valeur': inputs[2].value
        };
        parameters.push(param);
    }); 
    
    if (!selectedConfig || parameters.some(param => !param.Type || !param.Parametre || !param.Valeur)) {
        alert('Veuillez remplir tous les champs.');
        return; // Ne pas envoyer les données si les champs sont vides
    }

    if (parameters.some(param => !["string", "bool", "float", "integer"].includes(param.Type))) {
        alert('Veuillez entrer un type valide (string, bool, float, integer)');
        return;
    }

    // Création de l'objet FormData pour envoyer les données
    const formData = new FormData();
    formData.append('name_select', selectedConfig);
    formData.append('parameters', JSON.stringify(parameters));

    fetch('/save_version/', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.message);
            location.reload(); 
        }
    })
    .catch(error => {
        console.error('Erreur lors de l\'envoi des données:', error);
    });
}

const validateButton = document.getElementById('validate_version');

// Ajoutez un gestionnaire d'événements de clic au bouton "Valider"
validateButton.addEventListener('click', fetchVersionParameters);
function fetchVersionParameters() {
    // Récupérer la valeur sélectionnée (nom de la configuration)
    const selectedConfig = document.getElementById('name_select').value;
    const selectedVersion = document.getElementById('select_version').value;

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // Créez un objet d'en-tête pour inclure le jeton CSRF dans la demande
    const headers = new Headers({
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-CSRFToken': csrfToken, // Incluez le jeton CSRF ici
    });

    // Ensuite, utilisez l'objet d'en-tête dans votre requête fetch
    fetch('/get_selected_version_params/', {
        method: 'POST',
        headers: headers, // Utilisez les en-têtes avec le jeton CSRF
        body: `configName=${selectedConfig}&versionId=${selectedVersion}`,
    })
    .then(response => response.json())
    .then(data => {
        // Mettre à jour le tableau avec les paramètres reçus du serveur
        const configTable2 = document.getElementById('config-table2').getElementsByTagName('tbody')[0];
        configTable2.innerHTML = ''; // Effacez le contenu actuel de "config-table2"
        
        for (const param of data.parameters) {
            const newRow = configTable2.insertRow();
            const typeCell = newRow.insertCell(0);
            const parametreCell = newRow.insertCell(1);
            const valeurCell = newRow.insertCell(2);
        
            // Créez des éléments d'entrée pour chaque paramètre
            const typeInput = document.createElement('input');
            typeInput.type = 'text';
            typeInput.value = param.Type;
        
            const parametreInput = document.createElement('input');
            parametreInput.type = 'text';
            parametreInput.value = param.Parametre;
        
            const valeurInput = document.createElement('input');
            valeurInput.type = 'text';
            valeurInput.value = param.Valeur;
        
            // Vérifiez s'il y a plus d'une ligne dans le tableau
            if (configTable2.rows.length > 1) {
                // Créez un bouton "X" pour supprimer la ligne
                const deleteButton = document.createElement('button');
                deleteButton.className = 'delete-row';
                deleteButton.innerHTML = 'X';
                deleteButton.onclick = function() {
                    deleteRow(this);
                };
        
                // Ajoutez le bouton "X" à la quatrième cellule
                const deleteCell = newRow.insertCell(3);
                deleteCell.appendChild(deleteButton);
            }
        
            // Ajoutez les éléments d'entrée aux cellules du tableau
            typeCell.appendChild(typeInput);
            parametreCell.appendChild(parametreInput);
            valeurCell.appendChild(valeurInput);
        }
    })
    .catch(error => {
        console.error('Erreur lors de la récupération des paramètres:', error);
    });
}



document.addEventListener("DOMContentLoaded", function () {
    const activeTabIndex = localStorage.getItem('activeTabIndex');
    if (activeTabIndex !== null) {
        showTabContent(activeTabIndex);
    }
    displayTableNames(); 
});

function displayTableNames() {
    fetch('/get_table_names/')
        .then(response => response.json())
        .then(data => {
            if (data.table_names) {
                const tableNamesList = data.table_names;
                const selectElement = document.getElementById('name_select');
                const versionSelectElement = document.getElementById('select_version');
                versionSelectElement.innerHTML = ''; // Efface les anciennes options

                // Ajouter les options au <select> des configurations
                tableNamesList.forEach(tableName => {
                    const option = document.createElement('option');
                    option.value = tableName;
                    option.textContent = tableName;
                    selectElement.appendChild(option);
                });

                // Écouter les changements de sélection dans la première <select>
                selectElement.addEventListener('change', () => {
                    // Récupérer la valeur sélectionnée (nom de la configuration)
                    const selectedConfig = selectElement.value;

                    // Récupérer les versions associées à la configuration sélectionnée
                    const versionsForConfig = data.versions[selectedConfig] || [];

                    // Effacer les anciennes options de la deuxième <select>
                    versionSelectElement.innerHTML = '';

                    // Ajouter les options au <select> des versions
                    versionsForConfig.forEach(version => {
                        const option = document.createElement('option');
                        option.value = version;
                        option.textContent = `${version}`;
                        versionSelectElement.appendChild(option);
                    });
                });
            }
        })
        .catch(error => {
            console.error('Erreur lors de la récupération des configurations:', error);
        });
}

