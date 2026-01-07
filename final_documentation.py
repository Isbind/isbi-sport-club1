import os
import zipfile
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 16)
        self.cell(0, 10, 'Guide d\'Utilisation ISBISPORTCLUB', 0, 1, 'C')
        self.ln(5)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C')

def clean_text(text):
    """Nettoie le texte des caractères non-ASCII"""
    return ''.join(char for char in text if ord(char) < 128)

def create_documentation():
    # Créer le dossier de sortie
    os.makedirs('ISBISPORTCLUB_Documentation', exist_ok=True)
    
    # Créer le PDF
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Titre principal
    pdf.set_font('Arial', 'B', 24)
    pdf.cell(0, 20, 'Guide d\'Utilisation', 0, 1, 'C')
    pdf.set_font('Arial', 'B', 20)
    pdf.cell(0, 15, 'ISBISPORTCLUB', 0, 1, 'C')
    pdf.ln(10)
    
    # Table des matières
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 10, 'Table des matieres', 0, 1)
    pdf.set_font('Arial', '', 12)
    
    sections = [
        "1. Vue d'ensemble",
        "2. Installation",
        "3. Onglet Membres",
        "4. Onglet Abonnements",
        "5. Onglet Paiements",
        "6. Onglet Presences",
        "7. Tableau de Bord",
        "8. Conseils d'Utilisation",
        "9. Maintenance"
    ]
    
    for section in sections:
        pdf.cell(0, 10, clean_text(section), 0, 1)
    
    # Ajouter le contenu du README s'il existe
    readme_path = 'ISBISPORTCLUB_Documentation/README.md'
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        pdf.add_page()
        pdf.set_font('Arial', '', 12)
        
        for line in content.split('\n'):
            line = clean_text(line).strip()
            if not line:
                pdf.ln(5)
                continue
                
            if line.startswith('## '):
                pdf.set_font('Arial', 'B', 16)
                pdf.cell(0, 10, line[3:], 0, 1)
                pdf.set_font('Arial', '', 12)
            elif line.startswith('### '):
                pdf.set_font('Arial', 'B', 14)
                pdf.cell(0, 8, line[4:], 0, 1)
                pdf.set_font('Arial', '', 12)
            elif line.startswith(('- ', '* ')):
                pdf.cell(10)
                pdf.cell(0, 8, '- ' + line[2:], 0, 1)
            else:
                pdf.multi_cell(0, 8, line)
    
    # Sauvegarder le PDF
    pdf_path = 'ISBISPORTCLUB_Documentation/Guide_Utilisation_ISBISPORTCLUB.pdf'
    pdf.output(pdf_path)
    print(f"PDF genere avec succes : {pdf_path}")
    
    # Créer un fichier texte simple
    txt_path = 'ISBISPORTCLUB_Documentation/Guide_Utilisation_ISBISPORTCLUB.txt'
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write("GUIDE D'UTILISATION ISBISPORTCLUB\n")
        f.write("=" * 50 + "\n\n")
        
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as readme:
                f.write(readme.read())
    
    print(f"Fichier texte genere : {txt_path}")
    
    # Créer une archive ZIP
    zip_path = 'ISBISPORTCLUB_Documentation.zip'
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, dirs, files in os.walk('ISBISPORTCLUB_Documentation'):
            for file in files:
                zipf.write(
                    os.path.join(root, file),
                    os.path.relpath(os.path.join(root, file), 'ISBISPORTCLUB_Documentation')
                )
    
    print(f"Archive ZIP creee : {zip_path}")
    print("\nDocumentation prete a l'emploi !")

if __name__ == "__main__":
    create_documentation()
