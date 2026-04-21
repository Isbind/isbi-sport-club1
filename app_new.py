import sys
import os

# Ajouter le dossier ISBISPORTCLUB au chemin Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'ISBISPORTCLUB'))

# Importer et exécuter l'application principale
from app_new import main

if __name__ == '__main__':
    main()
