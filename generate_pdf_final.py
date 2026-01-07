import os
from fpdf import FPDF, FPDF_VERSION
from fpdf.enums import XPos, YPos
import markdown
from datetime import datetime
import re

class PDF(FPDF):
    def header(self):
        # Logo
        # self.image('logo.png', 10, 8, 33)
        # Police DejaVu pour supporter les caractères Unicode
        self.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        self.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)
        self.add_font('DejaVu', 'I', 'DejaVuSans-Oblique.ttf', uni=True)
        self.add_font('DejaVu', 'BI', 'DejaVuSans-BoldOblique.ttf', uni=True)
        
        # Titre
        self.set_font('DejaVu', 'B', 16)
        title = 'Guide d\'Utilisation ISBISPORTCLUB'
        self.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        self.ln(10)

    def footer(self):
        # Positionnement à 1,5 cm du bas
        self.set_y(-15)
        # Police DejaVu italique 8
        self.set_font('DejaVu', 'I', 8)
        # Numéro de page
        page_num = f'Page {self.page_no()}/{{nb}}'
        self.cell(0, 10, page_num, 0, 0, 'C')

def create_pdf():
    # Création du PDF
    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.add_page()
    
    # Titre principal
    pdf.set_font('DejaVu', 'B', 24)
    pdf.cell(0, 20, 'Guide d\'Utilisation', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.set_font('DejaVu', 'B', 20)
    pdf.cell(0, 15, 'ISBISPORTCLUB', new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
    pdf.ln(15)
    
    # Table des matières
    pdf.set_font('DejaVu', 'B', 16)
    pdf.cell(0, 10, 'Table des matières', new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font('DejaVu', '', 12)
    pdf.ln(5)
    
    # Sections
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
        # Nettoyer les émojis et caractères spéciaux
        clean_section = re.sub(r'[^\x00-\x7F]', '', section)  # Supprime les caractères non-ASCII
        pdf.cell(0, 10, clean_section, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    
    # Ajout du contenu du README
    with open('ISBISPORTCLUB_Documentation/README.md', 'r', encoding='utf-8') as file:
        md_content = file.read()
        
    # Conversion Markdown vers texte simple
    html = markdown.markdown(md_content)
    
    # Ajout du contenu au PDF
    pdf.add_page()
    pdf.set_font('DejaVu', '', 12)
    
    # Ajout du texte (version simplifiée)
    lines = md_content.split('\n')
    for line in lines:
        # Nettoyer la ligne des caractères non supportés
        clean_line = re.sub(r'[^\x00-\x7F]', '', line)  # Supprime les caractères non-ASCII
        
        if line.startswith('## '):
            pdf.set_font('DejaVu', 'B', 16)
            pdf.cell(0, 12, clean_line[3:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font('DejaVu', '', 12)
            pdf.ln(5)
        elif line.startswith('### '):
            pdf.set_font('DejaVu', 'B', 14)
            pdf.cell(0, 10, clean_line[4:], new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font('DejaVu', '', 12)
            pdf.ln(3)
        elif clean_line.strip() == '':
            pdf.ln(5)
        else:
            # Gérer les listes à puces
            if clean_line.strip().startswith(('- ', '* ')):
                pdf.cell(10)  # Indentation
                clean_line = '• ' + clean_line[2:]  # Remplacer par un point de puce standard
            
            # Écrire le texte avec gestion des sauts de ligne
            pdf.multi_cell(0, 5, clean_line)
            pdf.ln(2)
    
    # Sauvegarde du PDF
    output_file = 'ISBISPORTCLUB_Documentation/Guide_Utilisation_ISBISPORTCLUB.pdf'
    pdf.output(output_file)
    print(f"PDF généré avec succès : {output_file}")
    
    # Création d'une archive ZIP
    import shutil
    shutil.make_archive('ISBISPORTCLUB_Documentation', 'zip', 'ISBISPORTCLUB_Documentation')
    print("Archive ZIP créée avec succès : ISBISPORTCLUB_Documentation.zip")

if __name__ == "__main__":
    create_pdf()
