#!/usr/bin/env python3
"""
Point d'entrée principal pour l'application ISBISPORTCLUB
"""

import sys
import os

# Ajouter le dossier ISBISPORTCLUB au chemin Python
current_dir = os.path.dirname(os.path.abspath(__file__))
isbi_dir = os.path.join(current_dir, 'ISBISPORTCLUB')
sys.path.insert(0, isbi_dir)

try:
    # Importer le module principal
    import app_new
    
    # Exécuter l'application
    if __name__ == '__main__':
        app_new.main()
        
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print(f"Dossier courant: {current_dir}")
    print(f"Dossier ISBISPORTCLUB: {isbi_dir}")
    print(f"Chemin Python: {sys.path}")
    sys.exit(1)
except Exception as e:
    print(f"Erreur lors de l'exécution: {e}")
    sys.exit(1)
