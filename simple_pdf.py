from fpdf import FPDF
import os
import re

class PDF(FPDF):
    def header(self):
        # En-tête
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'Guide d\'Utilisation ISBISPORTCLUB', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        # Pied de page
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def clean_text(text):
    """Nettoie le texte des caractères non-ASCII et formate les listes"""
    # Remplacer les émojis par du texte descriptif
    emoji_map = {
        '📋': '[Liste]',
        '👥': '[Membres]',
        '💳': '[Abonnements]',
        '💰': '[Paiements]',
        '🏋️': '[Présences]',
        '📊': '[Tableau de bord]',
        '💡': '[Astuce]',
        '🔧': '[Maintenance]',
        '🌟': '[Important]',
        '💻': '[Installation]',
        '📋': '[Document]',
        '📌': '[Note]'
    }
    for emoji, replacement in emoji_map.items():
        text = text.replace(emoji, replacement)
    
    # Supprimer les autres caractères non-ASCII
    text = re.sub(r'[^\x00-\x7F]', ' ', text)
    return text.strip()

def create_simple_pdf():
    # Créer le dossier de sortie s'il n'existe pas
    os.makedirs('ISBISPORTCLUB_Documentation', exist_ok=True)
    
    # Créer le PDF
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Titre principal
    pdf.set_font('Helvetica', 'B', 24)
    pdf.cell(0, 20, 'Guide d\'Utilisation', 0, 1, 'C')
    pdf.set_font('Helvetica', 'B', 20)
    pdf.cell(0, 15, 'ISBISPORTCLUB', 0, 1, 'C')
    pdf.ln(10)
    
    # Table des matières
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, 'Table des matières', 0, 1)
    pdf.set_font('Helvetica', '', 12)
    
    sections = [
        "1. Vue d'ensemble",
        "2. Installation",
        "3. Onglet Membres",
        "4. Onglet Abonnements",
        "5. Onglet Paiements",
        "6. Onglet Présences",
        "7. Tableau de Bord",
        "8. Conseils d'Utilisation",
        "9. Maintenance"
    ]
    
    for section in sections:
        pdf.cell(0, 10, clean_text(section), 0, 1)
    
    # Lire le contenu du README
    try:
        with open('ISBISPORTCLUB_Documentation/README.md', 'r', encoding='utf-8') as file:
            content = file.read()
    except FileNotFoundError:
        content = "Le fichier de documentation n'a pas été trouvé."
    
    # Ajouter le contenu au PDF
    pdf.add_page()
    pdf.set_font('Helvetica', '', 12)
    
    # Traiter chaque ligne du contenu
    lines = content.split('\n')
    for line in lines:
        # Nettoyer la ligne
        clean_line = clean_text(line)
        
        if not clean_line.strip():
            pdf.ln(5)
            continue
            
        # Traiter les titres
        if line.startswith('## '):
            pdf.set_font('Helvetica', 'B', 16)
            pdf.cell(0, 10, clean_line[3:], 0, 1)
            pdf.set_font('Helvetica', '', 12)
            pdf.ln(2)
        elif line.startswith('### '):
            pdf.set_font('Helvetica', 'B', 14)
            pdf.cell(0, 8, clean_line[4:], 0, 1)
            pdf.set_font('Helvetica', '', 12)
            pdf.ln(2)
        # Traiter les listes
        elif line.strip().startswith(('- ', '* ')):
            pdf.cell(10)  # Indentation
            pdf.cell(0, 8, '• ' + clean_line[2:], 0, 1)
        else:
            # Texte normal
            pdf.multi_cell(0, 8, clean_line)
            pdf.ln(2)
    
    # Sauvegarder le PDF
    output_pdf = 'ISBISPORTCLUB_Documentation/Guide_Utilisation_ISBISPORTCLUB.pdf'
    pdf.output(output_pdf)
    print(f"PDF généré avec succès : {output_pdf}")
    
    # Créer une archive ZIP
    import zipfile
    with zipfile.ZipFile('ISBISPORTCLUB_Documentation.zip', 'w') as zipf:
        for root, dirs, files in os.walk('ISBISPORTCLUB_Documentation'):
            for file in files:
                zipf.write(os.path.join(root, file))
    
    print("Archive ZIP créée avec succès : ISBISPORTCLUB_Documentation.zip")

if __name__ == "__main__":
    create_simple_pdf()
