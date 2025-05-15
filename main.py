# main.py

import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk, simpledialog # Ajout de simpledialog pour les popups d'entrée
import json
import os

# --- 1. Chemin des dossiers et fichiers ---
PROFILES_DIR = "profiles" # Dossier où les profils seront stockés
# DATA_FILE ne sera plus une constante unique, mais dépendra du profil actif

# --- 2. Stockage des données (en mémoire) ---
games_collection = []
selected_game_index = -1 # Pour garder une trace de l'index du jeu sélectionné
current_profile = None # Variable pour stocker le nom du profil actif

# --- 3. Fonctions de gestion des profils ---

def get_profile_path(profile_name):
    """Retourne le chemin complet du fichier JSON pour un profil donné."""
    return os.path.join(PROFILES_DIR, f"{profile_name}.json")

def list_profiles():
    """Liste tous les profils disponibles dans le dossier PROFILES_DIR."""
    if not os.path.exists(PROFILES_DIR):
        os.makedirs(PROFILES_DIR) # Crée le dossier s'il n'existe pas
        return []
    
    profiles = []
    for filename in os.listdir(PROFILES_DIR):
        if filename.endswith(".json"):
            profiles.append(os.path.splitext(filename)[0]) # Enlève l'extension .json
    return sorted(profiles)

def create_profile():
    """Permet à l'utilisateur de créer un nouveau profil."""
    new_profile_name = simpledialog.askstring("Nouveau Profil", "Entrez le nom du nouveau profil :")
    if new_profile_name:
        new_profile_name = new_profile_name.strip()
        if not new_profile_name:
            messagebox.showwarning("Nom invalide", "Le nom du profil ne peut pas être vide.")
            return
            
        profile_path = get_profile_path(new_profile_name)
        if os.path.exists(profile_path):
            messagebox.showwarning("Profil existant", f"Un profil '{new_profile_name}' existe déjà.")
        else:
            try:
                with open(profile_path, 'w', encoding='utf-8') as f:
                    json.dump([], f) # Crée un fichier JSON vide pour le nouveau profil
                messagebox.showinfo("Succès", f"Profil '{new_profile_name}' créé.")
                refresh_profile_list() # Met à jour la combobox
                switch_profile(new_profile_name) # Passe automatiquement au nouveau profil
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur lors de la création du profil : {e}")

def delete_profile():
    """Permet à l'utilisateur de supprimer le profil sélectionné."""
    global current_profile
    selected_profile = profile_combobox.get()

    if not selected_profile:
        messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un profil à supprimer.")
        return
    
    if selected_profile == "Default": # Optionnel: Empêcher la suppression d'un profil par défaut
        messagebox.showwarning("Interdit", "Le profil 'Default' ne peut pas être supprimé.")
        return

    confirm = messagebox.askyesno(
        "Confirmer la suppression",
        f"Êtes-vous sûr de vouloir supprimer le profil '{selected_profile}' et toutes ses données ?"
    )

    if confirm:
        profile_path = get_profile_path(selected_profile)
        try:
            os.remove(profile_path)
            messagebox.showinfo("Succès", f"Profil '{selected_profile}' supprimé.")
            refresh_profile_list()
            # Si le profil supprimé était le profil actif, basculez vers un autre profil
            if current_profile == selected_profile:
                profiles = list_profiles()
                if profiles:
                    switch_profile(profiles[0]) # Bascule vers le premier profil disponible
                else:
                    current_profile = None # Aucun profil restant
                    games_collection.clear() # Vide la collection en mémoire
                    display_games() # Rafraîchit l'affichage
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur lors de la suppression du profil : {e}")

def refresh_profile_list():
    """Met à jour les options de la combobox des profils."""
    profiles = list_profiles()
    profile_combobox['values'] = profiles
    if not profiles:
        # Si aucun profil, crée un profil 'Default'
        if not os.path.exists(get_profile_path("Default")):
            with open(get_profile_path("Default"), 'w', encoding='utf-8') as f:
                json.dump([], f)
        profiles = list_profiles()
        profile_combobox['values'] = profiles

    if current_profile not in profiles and profiles:
        profile_combobox.set(profiles[0]) # Sélectionne le premier profil si l'actuel n'existe plus
    elif current_profile:
        profile_combobox.set(current_profile) # Reste sur le profil actuel si valide
    elif profiles:
        profile_combobox.set(profiles[0]) # Sélectionne le premier s'il n'y en a pas d'actuel

def switch_profile(profile_name_or_event=None):
    """Bascule vers le profil sélectionné et charge sa collection."""
    global current_profile
    
    if isinstance(profile_name_or_event, str):
        # Appel direct avec le nom du profil (ex: après création)
        profile_name = profile_name_or_event
    else:
        # Appel par événement ComboboxSelect
        profile_name = profile_combobox.get()

    if not profile_name:
        messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un profil.")
        return

    current_profile = profile_name
    print(f"Bascule vers le profil : {current_profile}")
    load_games()
    display_games()
    clear_entry_fields()
    button_add_update.config(text="Ajouter le jeu")
    selected_game_index = -1 # Réinitialise la sélection

# --- 4. Fonctions de gestion des données (Sauvegarde/Chargement) modifiées ---

def load_games():
    """Charge les jeux depuis le fichier JSON du profil actif."""
    global games_collection
    if not current_profile:
        games_collection = []
        return

    profile_data_file = get_profile_path(current_profile)
    if os.path.exists(profile_data_file):
        try:
            with open(profile_data_file, 'r', encoding='utf-8') as f:
                games_collection = json.load(f)
            print(f"Collection chargée depuis '{current_profile}'.json.")
        except json.JSONDecodeError:
            messagebox.showerror("Erreur de chargement", f"Fichier de données du profil '{current_profile}' corrompu. Création d'une nouvelle collection vide.")
            games_collection = []
        except Exception as e:
            messagebox.showerror("Erreur", f"Une erreur inattendue est survenue lors du chargement : {e}")
            games_collection = []
    else:
        # Cela ne devrait pas arriver si le profil est créé correctement
        print(f"Le fichier de données pour le profil '{current_profile}' n'existe pas. Création d'une nouvelle collection vide.")
        games_collection = []
        save_games() # Crée le fichier vide

def save_games():
    """Sauvegarde la collection actuelle dans le fichier JSON du profil actif."""
    if not current_profile:
        print("Aucun profil actif pour sauvegarder.")
        return

    profile_data_file = get_profile_path(current_profile)
    try:
        with open(profile_data_file, 'w', encoding='utf-8') as f:
            json.dump(games_collection, f, indent=4)
        print(f"Collection sauvegardée dans '{current_profile}'.json.")
    except Exception as e:
        messagebox.showerror("Erreur de sauvegarde", f"Impossible de sauvegarder la collection pour le profil '{current_profile}' : {e}")

# --- 5. Fonctions pour la gestion des jeux (ajout, affichage, modification, suppression) ---
# Ces fonctions restent globalement les mêmes, mais elles agissent sur la `games_collection`
# qui est maintenant liée au profil actif.

def add_or_update_game():
    """Ajoute un nouveau jeu ou met à jour un jeu existant."""
    global selected_game_index

    title = entry_title.get().strip()
    platform = entry_platform.get().strip()
    genre = entry_genre.get().strip()
    status = status_var.get()

    if not title or not platform:
        messagebox.showwarning("Entrée invalide", "Le titre et la plateforme sont obligatoires !")
        return
    
    if not current_profile:
        messagebox.showwarning("Aucun profil", "Veuillez créer ou sélectionner un profil avant d'ajouter des jeux.")
        return

    # Si un jeu est sélectionné, on le modifie
    if selected_game_index != -1:
        # Vérifier si les nouvelles infos ne créent pas un duplicata avec un autre jeu (sauf lui-même)
        for i, game in enumerate(games_collection):
            if i != selected_game_index and game['title'].lower() == title.lower() and \
               game['platform'].lower() == platform.lower():
                messagebox.showwarning("Jeu existant", f"Un autre jeu avec le titre '{title}' sur '{platform}' existe déjà.")
                return

        game_to_update = games_collection[selected_game_index]
        game_to_update['title'] = title
        game_to_update['platform'] = platform
        game_to_update['genre'] = genre if genre else "Non spécifié"
        game_to_update['status'] = status
        messagebox.showinfo("Succès", f"'{title}' a été mis à jour.")
        selected_game_index = -1 # Réinitialise la sélection après modification
        button_add_update.config(text="Ajouter le jeu") # Change le texte du bouton
    else: # Sinon, on ajoute un nouveau jeu
        # Vérifier si le jeu existe déjà (titre + plateforme)
        for game in games_collection:
            if game['title'].lower() == title.lower() and game['platform'].lower() == platform.lower():
                messagebox.showwarning("Jeu existant", f"Le jeu '{title}' sur '{platform}' est déjà dans votre collection.")
                return

        game = {
            "title": title,
            "platform": platform,
            "genre": genre if genre else "Non spécifié",
            "status": status
        }
        games_collection.append(game)
        messagebox.showinfo("Succès", f"'{title}' a été ajouté à votre collection.")

    save_games() # Sauvegarde après chaque ajout/modification
    clear_entry_fields() # Nettoie les champs
    display_games() # Rafraîchit l'affichage

def delete_game():
    """Supprime le jeu sélectionné de la collection."""
    global selected_game_index

    if selected_game_index == -1:
        messagebox.showwarning("Aucune sélection", "Veuillez sélectionner un jeu à supprimer dans la liste.")
        return
    
    if not current_profile:
        messagebox.showwarning("Aucun profil", "Veuillez créer ou sélectionner un profil.")
        return

    # Demande de confirmation avant la suppression
    confirm = messagebox.askyesno(
        "Confirmer la suppression",
        f"Êtes-vous sûr de vouloir supprimer '{games_collection[selected_game_index]['title']}' ?"
    )

    if confirm:
        del games_collection[selected_game_index]
        save_games() # Sauvegarde après suppression
        messagebox.showinfo("Succès", "Le jeu a été supprimé.")
        
        # Réinitialiser la sélection et l'interface
        selected_game_index = -1
        button_add_update.config(text="Ajouter le jeu")
        clear_entry_fields()
        tree.selection_remove(tree.selection()) # Désélectionne dans le Treeview
        display_games() # Rafraîchit l'affichage
    else:
        # L'utilisateur a annulé la suppression
        pass


def clear_entry_fields():
    """Nettoie les champs d'entrée."""
    entry_title.delete(0, tk.END)
    entry_platform.delete(0, tk.END)
    entry_genre.delete(0, tk.END)
    status_var.set("Possédé") # Réinitialise le statut par défaut

def display_games():
    """Affiche tous les jeux de la collection dans le Treeview."""
    for item in tree.get_children():
        tree.delete(item)

    if not games_collection:
        print("Votre collection de jeux est vide pour l'instant.")
        return

    sorted_games = sorted(games_collection, key=lambda x: x['title'].lower())

    for i, game in enumerate(sorted_games):
        # On stocke l'index réel du jeu dans la liste non triée pour faciliter la modification/suppression
        tree.insert("", "end", iid=str(i),
                    values=(game['title'], game['platform'], game['genre'], game['status']),
                    tags=(str(games_collection.index(game)),) # Stocke l'index original comme un tag
                    )

def select_game_from_tree(event):
    """Charge les informations du jeu sélectionné dans les champs d'entrée."""
    global selected_game_index
    selected_items = tree.selection()

    if selected_items:
        selected_item_id = selected_items[0]
        
        # Récupérer l'index original du jeu à partir des tags de la ligne sélectionnée
        original_index_tag = tree.item(selected_item_id, 'tags')[0]
        selected_game_index = int(original_index_tag)

        game = games_collection[selected_game_index]

        clear_entry_fields() # Nettoie d'abord les champs
        entry_title.insert(0, game['title'])
        entry_platform.insert(0, game['platform'])
        entry_genre.insert(0, game['genre'])
        status_var.set(game['status'])
        
        button_add_update.config(text="Modifier le jeu")
    else:
        selected_game_index = -1
        button_add_update.config(text="Ajouter le jeu")
        clear_entry_fields()


# --- 6. Configuration de la fenêtre principale ---

root = tk.Tk()
root.title("Mon Gestionnaire de Collection de Jeux")
root.geometry("800x750")
root.resizable(True, True)

# --- 7. Widgets de gestion des profils ---
profile_frame = tk.LabelFrame(root, text="Gestion des Profils", padx=10, pady=5)
profile_frame.pack(pady=10, padx=10, fill="x")

tk.Label(profile_frame, text="Profil actif :").pack(side="left", padx=5)

profile_combobox = ttk.Combobox(profile_frame, width=25, state="readonly")
profile_combobox.pack(side="left", padx=5)
profile_combobox.bind("<<ComboboxSelected>>", switch_profile) # Lance le changement de profil

tk.Button(profile_frame, text="Créer Profil", command=create_profile).pack(side="left", padx=5)
tk.Button(profile_frame, text="Supprimer Profil", command=delete_profile, bg="orange", fg="white").pack(side="left", padx=5)


# --- 8. Widgets d'ajout/modification/suppression de jeux ---
input_frame = tk.LabelFrame(root, text="Ajouter / Modifier un jeu", padx=10, pady=10)
input_frame.pack(pady=10, padx=10, fill="x")

tk.Label(input_frame, text="Titre du jeu :").grid(row=0, column=0, sticky="w", pady=2)
entry_title = tk.Entry(input_frame, width=60)
entry_title.grid(row=0, column=1, pady=2)

tk.Label(input_frame, text="Plateforme :").grid(row=1, column=0, sticky="w", pady=2)
entry_platform = tk.Entry(input_frame, width=60)
entry_platform.grid(row=1, column=1, pady=2)

tk.Label(input_frame, text="Genre :").grid(row=2, column=0, sticky="w", pady=2)
entry_genre = tk.Entry(input_frame, width=60)
entry_genre.grid(row=2, column=1, pady=2)

tk.Label(input_frame, text="Statut :").grid(row=3, column=0, sticky="w", pady=2)
status_frame = tk.Frame(input_frame)
status_frame.grid(row=3, column=1, sticky="w", pady=2)

status_var = tk.StringVar(value="Possédé")
tk.Radiobutton(status_frame, text="Possédé", variable=status_var, value="Possédé").pack(side="left", padx=5)
tk.Radiobutton(status_frame, text="En cours", variable=status_var, value="En cours").pack(side="left", padx=5)
tk.Radiobutton(status_frame, text="Fini", variable=status_var, value="Fini").pack(side="left", padx=5)
tk.Radiobutton(status_frame, text="Souhaité", variable=status_var, value="Souhaité").pack(side="left", padx=5)

button_frame = tk.Frame(input_frame)
button_frame.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")

button_add_update = tk.Button(button_frame, text="Ajouter le jeu", command=add_or_update_game)
button_add_update.pack(side="left", padx=5, expand=True)

button_delete = tk.Button(button_frame, text="Supprimer le jeu", command=delete_game, bg="red", fg="white")
button_delete.pack(side="left", padx=5, expand=True)

button_clear_selection = tk.Button(button_frame, text="Nouvel ajout", command=lambda: (clear_entry_fields(), button_add_update.config(text="Ajouter le jeu"), tree.selection_remove(tree.selection()), globals().__setitem__('selected_game_index', -1)))
button_clear_selection.pack(side="left", padx=5, expand=True)


# --- 9. Widgets d'affichage des jeux ---
display_frame = tk.LabelFrame(root, text="Votre collection", padx=10, pady=10)
display_frame.pack(pady=10, padx=10, fill="both", expand=True)

columns = ('Titre', 'Plateforme', 'Genre', 'Statut')
tree = ttk.Treeview(display_frame, columns=columns, show='headings', selectmode='browse')

for col in columns:
    tree.heading(col, text=col, anchor='w')
    tree.column(col, width=150, minwidth=100, stretch=True)

scrollbar_y = ttk.Scrollbar(display_frame, orient="vertical", command=tree.yview)
scrollbar_x = ttk.Scrollbar(display_frame, orient="horizontal", command=tree.xview)
tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)

tree.grid(row=0, column=0, sticky='nsew')
scrollbar_y.grid(row=0, column=1, sticky='ns')
scrollbar_x.grid(row=1, column=0, sticky='ew')

display_frame.grid_rowconfigure(0, weight=1)
display_frame.grid_columnconfigure(0, weight=1)

tree.bind('<<TreeviewSelect>>', select_game_from_tree)

# --- 10. Initialisation au démarrage ---

# S'assurer que le dossier des profils existe
if not os.path.exists(PROFILES_DIR):
    os.makedirs(PROFILES_DIR)

# Si aucun profil n'existe, créer un profil "Default"
if not list_profiles():
    with open(get_profile_path("Default"), 'w', encoding='utf-8') as f:
        json.dump([], f)

refresh_profile_list() # Charge la liste des profils dans la combobox
initial_profiles = list_profiles()
if initial_profiles:
    switch_profile(initial_profiles[0]) # Charge le premier profil disponible au démarrage
else:
    # Cas exceptionnel où même la création du profil par défaut échouerait
    messagebox.showerror("Erreur", "Impossible de charger ou créer un profil. L'application va se fermer.")
    root.destroy()

root.mainloop()