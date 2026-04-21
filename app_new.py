import sys
import os

# Ajouter le dossier ISBISPORTCLUB au chemin Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'ISBISPORTCLUB'))

# Importer et exécuter l'application principale
# Utiliser un nom de module différent pour éviter l'import circulaire
import app_new as isbi_app

if __name__ == '__main__':
    isbi_app.main()
