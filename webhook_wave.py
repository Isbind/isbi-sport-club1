import sys
import os

# Ajouter le dossier ISBISPORTCLUB au chemin Python
sys.path.append(os.path.join(os.path.dirname(__file__), 'ISBISPORTCLUB'))

# Importer et exécuter le module webhook
from webhook_wave import *
