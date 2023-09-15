from django.shortcuts import render
from django.http import JsonResponse
import os
from datetime import datetime
import zipfile
import json
from pathlib import Path
import shutil
import subprocess
from django.views.decorators.http import require_POST
from django.core.files.storage import FileSystemStorage
from django.views.decorators.csrf import csrf_exempt
from .models import Folder
from tinydb import TinyDB, Query
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.conf import settings
import numpy as np
from PIL import Image
import imageio
import cv2
import pyexr
import matplotlib.pyplot as plt
import time
import re
COLOR_MAP = 'viridis'


os.environ['OPENCV_IO_ENABLE_OPENEXR'] = 'TRUE'

def collect_configurations():
    db = TinyDB('configurations.json')
    table_names = db.tables()

    configurations = []

    for table_name in table_names:
        config_versions = []
        records = db.table(table_name).all()

        for record in records:
            version_id = int(record.doc_id)
            parameters = json.loads(record['config']['parameters'])
            config_versions.append({
                'version_id': version_id,
                'parameters': parameters
            })

        configurations.append({
            'name': table_name,
            'versions': config_versions
        })

    return configurations

def accueil(request):
    return render(request, 'accueil.html')

def scene(request):
    directory_path = os.path.join(".", "media" ,"scene")
    folders = [folder for folder in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, folder))]
    folders.sort()
    return render(request, 'scene.html', {'folders': folders})

def configuration(request):
    configurations = collect_configurations()
    return render(request, 'configuration.html', {'configurations': configurations})

def generation(request):  
    db = TinyDB('configurations.json')
    table_names = db.tables()

    table_versions = []

    for table_name in table_names:
        table = db.table(table_name)
        versions = table.all()
        for version in versions:
            version_name = f"{table_name}.{version.doc_id}"
            table_versions.append(version_name)
    
    directory_path = os.path.join(".", "media" ,"scene")
    folders = [folder for folder in os.listdir(directory_path) if os.path.isdir(os.path.join(directory_path, folder))]
    
    configurations = collect_configurations()
    return render(request, 'generation.html', {'table_versions': table_versions, 'folders': folders, 'configurations': configurations})

def comparaison(request):
    if request.method == 'GET':
        source_path = os.path.join(".", "media" ,"rendus")
        if os.path.exists(source_path):
            folders = [f for f in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, f))]
            configurations = collect_configurations()
            return render(request, 'comparaison.html', {'folders': folders, 'configurations': configurations})
    return render(request, 'comparaison.html', {'folders': []}) 

def get_image(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))  
            folder_name = data.get('folderName')
            print('Folder Name:', folder_name)

            if folder_name is None:
                return JsonResponse({'success': False, 'error': 'Folder name is missing.'})

            image_url = os.path.join("..", "media", "scene", folder_name, folder_name + ".png").replace("\\", "/")
            print('url:', image_url)

            return JsonResponse({'success': True, 'imageURL': image_url})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON data.'})

    return JsonResponse({'success': False})

@require_POST
def delete_folder_view(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        folder_name = request.POST.get('folderName')
        directory_path = os.path.join(".", "media" ,"scene")

        try:
            folder_path = os.path.join(directory_path, folder_name)
            if os.path.exists(folder_path):
                shutil.rmtree(folder_path)
                return JsonResponse({'success': True, 'message': 'Le dossier a été supprimé avec succès.'})
            else:
                return JsonResponse({'success': False, 'error': 'Le dossier n\'existe pas.'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Requête non valide.'})

def exr_to_png(exr_file, png_file):
    # Chargez l'image EXR
    exr_image = pyexr.open(exr_file).get()

    # Tonemap l'image EXR en une image LDR (8 bits par canal)
    ldr_image = (np.power(np.clip(exr_image,0,1), 1/2.2) * 255).astype(np.uint8)

    # Créez une image Pillow à partir de l'array NumPy
    img = Image.fromarray(ldr_image, 'RGB')

    # Enregistrez l'image au format PNG
    img.save(png_file, format='PNG')    

@require_POST
def upload_zip_file(request):
    directory_path = os.path.join(".", "media" ,"scene")
    if request.method == 'POST' and request.FILES.get('zip_file'):
        new_name = request.POST.get('Name')
        image_file = request.FILES['image_file']
        original_filename, file_extension = os.path.splitext(image_file.name)

        zip_file = request.FILES['zip_file']
        ancien_nom = zip_file.name
                      
        try:
            # Ouvrir le fichier .zip
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                # Vérifier si un fichier avec l'extension .pbrt existe dans le zip
                for file_name in zip_ref.namelist():
                    if file_name.lower().endswith('scene.pbrt'):
                        if os.path.exists(os.path.join(directory_path, new_name)):
                            return JsonResponse({'success': False, 'error': 'Un dossier avec le nom existe déjà dans le répertoire cible'})
                        else:
                            
                            dossier_tempo = os.path.join(directory_path, "tempo")
                            os.makedirs(dossier_tempo)                           
                            zip_ref.extractall(dossier_tempo)
                            os.rename(os.path.join(dossier_tempo , ancien_nom[:-4]) , os.path.join(directory_path , new_name) )
                            os.rmdir(dossier_tempo) 
                            
                            with open(os.path.join(directory_path, new_name, 'scene.pbrt'), 'r') as scene_file:
                                scene_content = scene_file.read()
                                
                            if '%%PARAMS%%' in scene_content and '%%OUTPUT%%' in scene_content:                                                               
                                with open(os.path.join(directory_path , new_name, image_file.name), 'wb') as destination_file:
                                    shutil.copyfileobj(image_file, destination_file)
                                os.rename(os.path.join(directory_path , new_name, image_file.name) , os.path.join(directory_path , new_name, new_name+file_extension))
                                
                                if file_extension == ".exr":
                                   exr_to_png(os.path.join(directory_path , new_name, new_name+file_extension), os.path.join(directory_path , new_name, new_name+".png")) 
                                         
                                message = "Le type de fichier scene.pbrt est présent dans le dossier .zip."
                                return JsonResponse({'success': True, 'message': message})
                            else :
                                shutil.rmtree(os.path.join(directory_path, new_name))
                                message = "Le fichier scene.pbrt ne contient pas les indices %%PARAMS%% et %%OUTPUT%%."
                                return JsonResponse({'success': False, 'error': message})
                                    
            # Aucun fichier .pbrt trouvé dans le zip
            message = "Le type de fichier scene.pbrt n'est pas présent dans le dossier .zip."
            return JsonResponse({'success': False,'error': message})
            
        except zipfile.BadZipFile:
            message = "Le fichier téléchargé n'est pas un fichier .zip valide."
            return JsonResponse({'success': False,'error': message}, status=400)
        except Exception as e:
            message = "Une erreur s'est produite lors de la vérification du fichier .zip."
            shutil.rmtree(os.path.join(directory_path, "tempo"))
            return JsonResponse({'success': False,'error': message}, status=500)

    # Réponse JSON en cas d'erreur ou si le formulaire n'est pas correctement rempli
    return JsonResponse({'success': False,'error': 'Une erreur s\'est produite lors de la vérification du fichier .zip.'}, status=400)

@csrf_exempt
def save_configuration(request):
    if request.method == 'POST':
        data = request.POST
        name_config = data.get('name_config')
        
        # Vérifier si le nom de configuration existe déjà dans la base de données
        db = TinyDB('configurations.json')
        if db.table(name_config):
            return JsonResponse({'error': 'Erreur : la configuration existe.'}, status=400)
        
        table = db.table(name_config) 

        # Enregistrement des paramètres dans la base de données TinyDB
        doc_id = table.insert({ 'config': data.dict()})
        version_data = table.get(doc_id = int (doc_id))
        
        chemin_dossier = os.path.join(".", "media" ,"rendus", name_config + "." + str(doc_id))
        os.makedirs(chemin_dossier, exist_ok=True)

        return JsonResponse({'message': 'Configuration enregistrée avec succès!'})
    else:
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
    
@csrf_exempt
def save_version(request):
    if request.method == 'POST':
        data = request.POST
        name_select = data.get('name_select')
        
        db = TinyDB('configurations.json')       
        table = db.table(name_select)   
        
        # Enregistrement des paramètres dans la base de données TinyDB
        doc_id = table.insert({ 'config': data.dict()})
        version_data = table.get(doc_id = int (doc_id))
        
        chemin_dossier = os.path.join(".", "media" ,"rendus", name_select + "." + str(doc_id))
        os.makedirs(chemin_dossier, exist_ok=True)
        
        return JsonResponse({'message': 'Configuration enregistrée avec succès!'})
    else:
        return JsonResponse({'error': 'Méthode non autorisée'}, status=405)
           
def get_table_names(request):
    db = TinyDB('configurations.json')
    
    # Obtenez les noms de configuration
    table_names_set = db.tables()
    table_names_list = list(table_names_set)
    
    # Obtenez les versions associées à chaque configuration
    versions = {}
    for table_name in table_names_list:
        table = db.table(table_name)
        versions[table_name] = [item.doc_id for item in table]
    
    return JsonResponse({'table_names': table_names_list, 'versions': versions})

@require_POST
def get_parameters(request):
    selected_versions = request.POST.getlist('selected_versions[]')
    selected_folders = request.POST.getlist('selected_folders[]')
    engine_url = request.POST.get('engine_url')
    maintenant = datetime.now()
    date = maintenant.strftime("%Y-%m-%d_%H-%M-%S")
    db = TinyDB('configurations.json')
    parameters = {}
    # Vérifiez si l'URL du moteur est valide
    if not os.path.exists(engine_url):
        return JsonResponse({'success': False, 'message': 'L\'URL du moteur est invalide.'})
        
    
    for version_name in selected_versions:
        table_name, version_number = version_name.split('.')
        table = db.table(table_name)
        version_data = table.get(doc_id=int(version_number))
        if version_data:
            params_list = json.loads(version_data['config']['parameters'])
            parameters[version_name] = params_list
            
            tempo = os.path.join(".", "media" ,"rendus", version_name, "tempo")
            os.makedirs(tempo, exist_ok=True)
            os.makedirs(os.path.join(".", "media" ,"rendus", version_name, date ) , exist_ok=True)
            
            
            for folder_name in selected_folders:
                folder_path = os.path.join(".", "media" ,"scene", folder_name)
                nouveau = shutil.copytree(folder_path, os.path.join(tempo, folder_name))
                scene_file_path = os.path.join(tempo, folder_name, 'scene.pbrt')
                if folder_name+".exr" in os.listdir(nouveau):
                    output = os.path.join(".", "media" ,"rendus", version_name, date, folder_name +'.exr' )
                else:
                    output = os.path.join(".", "media" ,"rendus", version_name, date, folder_name +'.png' ) 
                                                   
                with open(scene_file_path, 'r') as f:
                    scene_content = f.read()
                    
                integrator_line = f'Integrator "{table_name}"\n'
                scene_content = scene_content.replace('%%PARAMS%%', integrator_line, 1)

                for param in params_list:
                    param_text = f"{param['Type']} : {param['Parametre']} : {param['Valeur']}"
                    if param['Type'] == "string":
                        scene_content = scene_content.replace('\n', f"\n\t\"{param['Type']} {param['Parametre']}\" [ \"{param['Valeur']}\" ]\n", 1)  # Add param on new line
                    else:
                        scene_content = scene_content.replace('\n', f"\n\t\"{param['Type']} {param['Parametre']}\" [ {param['Valeur']} ]\n", 1)  # Add param on new line
                output_for_scene = output.replace('\\', '/')
                scene_content = scene_content.replace('%%OUTPUT%%', f'"{output_for_scene}"' )
                with open(scene_file_path, 'w') as f:
                    f.write(scene_content)
                
                
                
                commande = [engine_url, scene_file_path]
                subprocess.run(commande, shell=True)               
            shutil.rmtree(tempo)
                
    return JsonResponse({'success': True})

def get_subfolders(request):
    source_folder = request.GET.get('source')
    subfolders = []

    if source_folder:
        source_path = os.path.join(".", "media" ,"rendus", source_folder)
        if os.path.exists(source_path):
            subfolders = [f for f in os.listdir(source_path) if os.path.isdir(os.path.join(source_path, f))]

    return JsonResponse(subfolders, safe=False)

def get_image_names(request):
    selected_folders = request.GET.getlist('selected_folder')
    selected_subfolders = request.GET.getlist('selected_subfolder')
    print(selected_subfolders)
    image_names = []

    if len(selected_folders) == len(selected_subfolders) and len(selected_folders) > 0:
        for i, selected_folder in enumerate(selected_folders):
            selected_subfolder = selected_subfolders[i]
            subfolder_path = os.path.join(settings.MEDIA_ROOT, "rendus", selected_folder, selected_subfolder)
            image_files = [f for f in os.listdir(subfolder_path) if f.lower().endswith('.png')]
            image_names.extend(image_files)

    return JsonResponse(image_names, safe=False)

def view_all_images(request):
    selected_folders = request.GET.getlist('selected_folder')
    selected_subfolders = request.GET.getlist('selected_subfolder')
    selected_options = request.GET.get('selected_options', '').split(',')
    


    if len(selected_folders) == len(selected_subfolders) and len(selected_folders) > 1:
        image_data = {}

        for i, selected_folder in enumerate(selected_folders):
            selected_subfolder_list = selected_subfolders[i].split(';')
            subfolder_path = "/".join(selected_subfolder_list)
            subfolder_path = subfolder_path.replace(':', ';')
            base_path = os.path.join(settings.MEDIA_ROOT, "rendus", selected_folder, subfolder_path)
            image_files = []
    
            for f in os.listdir(base_path):
                if f.lower().endswith('.png'):
                    # Vérifiez si un fichier .exr existe avec le même nom (en supprimant l'extension .png)
                    exr_filename = f[:f.rfind('.png')] + '.exr'
                    exr_path = os.path.join(base_path, exr_filename)
                    if not os.path.exists(exr_path):
                        # Si le fichier .exr correspondant n'existe pas, ajoutez le .png à la liste
                        image_files.append(f)
                elif f.lower().endswith('.exr'):
                    image_files.append(f)
                
                
            for image_file in image_files:
                image_name = os.path.splitext(image_file)[0]
                image_path = os.path.join(settings.MEDIA_URL, "rendus", selected_folder, subfolder_path, image_file).replace("\\", "/")

                if image_name not in image_data:
                    image_data[image_name] = {}

                # Create the key using selected_folder and subfolder_name
                subfolder_name = selected_folder + "_" + selected_subfolder_list[-1]

                if subfolder_name not in image_data[image_name]:
                    image_data[image_name][subfolder_name] = []
                
                image_data[image_name][subfolder_name].append(image_path)

        # Remove images not present in all other selected subfolders
        filtered_image_data = {}
        for image_name, subfolder_data in image_data.items():
            all_subfolders_exist = all(selected_folder + "_" + selected_subfolders[i].split(';')[-1] in subfolder_data for i, selected_folder in enumerate(selected_folders))
            if all_subfolders_exist:
                filtered_image_data[image_name] = subfolder_data  
                
        context = {
            'image_data': filtered_image_data,
        }
        new_image_data = traiter_contexte(context)
        #print(new_image_data)
        metric_results = {}

        for image_name, subfolder_data in context.get('image_data', {}).items():
            if os.path.isfile(os.path.join(".", "media" ,"scene", image_name , f"{image_name}.exr")):
                reference_image_path = os.path.join(".", "media" ,"scene", image_name , f"{image_name}.exr")
            else:
                reference_image_path = os.path.join(".", "media" ,"scene", image_name , f"{image_name}.png")  
            for subfolder_name, image_info_list in subfolder_data.items():
                    image_info = image_info_list[0]
                    chemin_image = image_info.get('chemin', '')
                                       
                    chemin = os.path.dirname(chemin_image[1:])                    
                    if not os.path.exists(os.path.join(chemin,image_name)):
                        os.makedirs(os.path.join(chemin,image_name), exist_ok=True)   
                    #metrics = ['l1', 'l2', 'mrse', 'mape']  
                    metric_results[image_name] = {}
                    for metric in selected_options:
                        if not metric == "negpos":
                            error = compute_metric_from_files(reference_image_path, chemin_image[1:], metric, 1e-2)
                            err_mean = np.mean(error)  
                            fc = falsecolor(error, [0, 1], 1e-2)
                        else:
                            fc = falsecolor_np(reference_image_path, chemin_image[1:], eps=1e-2)
                            
                        output = os.path.join(chemin ,image_name , metric + ".png")
                        print("chemin et metric ", chemin_image, metric)
                        plt.imsave(output, fc)
                        
                        # Créez une nouvelle image_info_list pour stocker le nouveau chemin et titre
                        new_image_info = {'chemin': os.path.join(os.path.dirname(chemin_image) ,image_name , metric + ".png").replace("\\", "/"), 'titre': metric.upper()}

                        # Ajoutez la nouvelle image_info à subfolder_name
                        if subfolder_name not in context['image_data'][image_name]:
                            context['image_data'][image_name][subfolder_name] = []
                        context['image_data'][image_name][subfolder_name].append(new_image_info)
                        
                        """# Stocker le résultat dans un dictionnaire avec une structure appropriée
                        if metric not in metric_results[image_name]:
                            metric_results[image_name][metric] = {}
                        if subfolder_name not in metric_results[image_name][metric]:
                            metric_results[image_name][metric][subfolder_name] = {}
                        metric_results[image_name][metric][subfolder_name][image_path] = error"""
                    
                     
        for image_name, subfolder_data in context.get('image_data', {}).items():
            for subfolder_name, image_info_list in subfolder_data.items():
                for image_info in image_info_list:
                    chemin_image = image_info.get('chemin', '')
                    new_image_paths = []  # Liste pour stocker les nouveaux chemins d'images                   
                    if chemin_image.lower().endswith('.exr'):
                        png_file_path = os.path.splitext(chemin_image[1:])[0] + '.png'
                        if not os.path.exists(png_file_path):
                            exr_to_png(chemin_image[1:], png_file_path)
                        new_image_path = '/' + png_file_path
                        image_info['chemin'] = new_image_path                     
            
        
        
        for image_name, subfolder_data in context.get('image_data', {}).items():
            # Créez un dictionnaire pour la référence au même niveau que les sous-dossiers
            subfolder_data["Reference"] = []
            # Ajoutez le chemin d'accès à la référence (par exemple, une image PNG)
            subfolder_data["Reference"].append({'chemin': os.path.join("/media" ,"scene", image_name , f"{image_name}.png").replace("\\", "/"), 'titre': 'Image'})
            
        #traiter_contexte(context)
        print(context)
        return render(request, 'image_gallery.html', context)
    return render(request, 'image_gallery.html', {'error_message': 'Invalid selection'})

def check_image_presence(request):
    selected_folders = request.GET.getlist('selected_folder')
    selected_subfolders = request.GET.getlist('selected_subfolder')

    images_to_display = set()
    images_not_displayed = set()
    image_missing_info = {}  # Nouveau dictionnaire pour stocker les dossiers manquants par image

    if len(selected_subfolders) >= 2:
        all_images = {}  # Dictionnaire pour stocker les images de chaque sous-dossier

        for i, selected_folder in enumerate(selected_folders):
            selected_subfolder_list = selected_subfolders[i].split(';')
            subfolder_path = "/".join(selected_subfolder_list)
            subfolder_path = subfolder_path.replace(':', ';')
            base_path = os.path.join(settings.MEDIA_ROOT, "rendus", selected_folder, subfolder_path)
                   
            image_files = []
    
            for f in os.listdir(base_path):
                if f.lower().endswith('.png'):
                    # Vérifiez si un fichier .exr existe avec le même nom (en supprimant l'extension .png)
                    exr_filename = f[:f.rfind('.png')] + '.exr'
                    exr_path = os.path.join(base_path, exr_filename)
                    if not os.path.exists(exr_path):
                        # Si le fichier .exr correspondant n'existe pas, ajoutez le .png à la liste
                        image_files.append(f)
                elif f.lower().endswith('.exr'):
                    image_files.append(f)
            
            all_images[selected_subfolders[i]] = image_files

        for subfolder in selected_subfolders:
            for image in all_images[subfolder]:
                missing_subfolders = set(selected_subfolders)
                missing_subfolders.remove(subfolder)

                for other_subfolder in missing_subfolders:
                    if image not in all_images[other_subfolder]:
                        images_not_displayed.add(image)
                        if image not in image_missing_info:
                            image_missing_info[image] = []
                        image_missing_info[image].append(f"{selected_folders[selected_subfolders.index(other_subfolder)]}/{other_subfolder}")

                if image not in images_not_displayed:
                    images_to_display.add(image)

    data = {
        'images_to_display': list(images_to_display),
        'images_not_displayed': list(images_not_displayed),
        'image_missing_info': image_missing_info,
    }

    return JsonResponse(data)

def compute_metric_from_files(ref_path, test_path, metric, eps):
    
    # Charger les images de référence et de test en fonction de leurs extensions
    ref = load_img(ref_path)
    test = load_img(test_path)
    # Assurez-vous que les images ont la même taille
    if ref.shape != test.shape:
        raise ValueError("Les images de référence et de test doivent avoir la même taille.")
    # Calculer la différence entre les images
    diff = np.array(ref - test)

    if metric == 'l1':
        error = np.abs(diff)
    elif metric == 'l2':
        error = diff * diff
    elif metric == 'mrse':
        error = diff * diff / (ref * ref + eps)
    elif metric == 'mape':
        error = np.abs(diff) / (ref + eps)
    elif metric == 'smape':
        error = 2 * np.abs(diff) / (ref + test + eps)
    else:
        raise ValueError('Métrique invalide')

    return error

def falsecolor(error, clip, eps):
    """Compute false color heatmap."""
    cmap = plt.get_cmap(COLOR_MAP)
    mean = np.mean(error, axis=2)
    min_val, max_val = clip
    val = np.clip((mean - min_val) / (max_val - min_val + eps), 0, 1)
    return cmap(val)

def load_img(filepath):
    """Load HDR or LDR image (either .hdr or .exr for HDR or .png for LDR)."""

    if filepath.endswith('.exr'):
        fp = pyexr.open(filepath)
        img = np.array(fp.get(), dtype=np.float64)
    elif filepath.endswith('.hdr'):
        fp = cv2.imread(filepath, cv2.IMREAD_ANYDEPTH)
        fp = cv2.cvtColor(fp, cv2.COLOR_BGR2RGB)
        img = np.array(fp, dtype=np.float64)
    elif filepath.endswith('.png'):
        fp = cv2.imread(filepath)
        fp = cv2.cvtColor(fp, cv2.COLOR_BGR2RGB)
        # important to be signed, because some metrics' calculations can have intermediate negative values.
        img = np.array(fp, dtype=np.int32)
    else:
        raise Exception('Only HDR and OpenEXR and PNG images are supported')

    return img

def traiter_contexte(contexte):
    image_data = contexte.get('image_data', {})

    # Créer une nouvelle structure de données avec les chemins d'image et le titre "Image"
    new_image_data = {}
    for image_name, folder_data in image_data.items():
        new_folder_data = {}
        for folder_name, image_paths in folder_data.items():
            new_image_paths = [{'chemin': path, 'titre': 'Image'} for path in image_paths]
            new_folder_data[folder_name] = new_image_paths
        new_image_data[image_name] = new_folder_data

    contexte['image_data'] = new_image_data
    return contexte

def get_selected_version_params(request):
    config_name = request.POST.get('configName')  # Le nom de la configuration, par exemple, "path"
    version_id = request.POST.get('versionId')    # L'ID de la version, par exemple, "1"

    db = TinyDB('configurations.json')
    
    # Assurez-vous que la configuration existe dans la base de données
    if config_name in db.tables():
        table = db.table(config_name)
        version_data = table.get(doc_id=version_id)
            
        print(version_id)
            # Vérifiez si la version a un champ "config" avec des données JSON
        if 'config' in version_data:
            parameters = json.loads(version_data['config']['parameters'])
            return JsonResponse({'parameters': parameters})
      

def falsecolor_np(ref_path, test_path, eps=1e-2):
    """Compute negative / positive relative error."""
    ref = load_img(ref_path)
    test = load_img(test_path)
    
    diff = 2 * np.array(test - ref) / (ref + test + eps)
    diff = np.mean(diff, axis=2)
    diff = np.clip(diff, -1, 1)

    img = np.zeros((diff.shape[0], diff.shape[1], 3))
    img[diff > 0, 0] = diff[diff > 0]
    img[diff < 0, 1] = -diff[diff < 0]
    return img
