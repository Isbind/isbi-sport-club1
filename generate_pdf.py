import os
from weasyprint import HTML
import markdown

def convert_md_to_pdf(md_file, pdf_file):
    # Lire le contenu du fichier Markdown
    with open(md_file, 'r', encoding='utf-8') as f:
        md_content = f.read()
    
    # Convertir Markdown en HTML
    # Créer le contenu HTML avec mise en forme
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Guide d'Utilisation ISBISPORTCLUB</title>
        <style>
            @page {{
                size: A4;
                margin: 2cm;
                @bottom-right {{
                    content: "Page " counter(page) " sur " counter(pages);
                    font-size: 10pt;
                }}
            }}
            body {{ 
                font-family: Arial, sans-serif;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
                color: #333;
                font-size: 11pt;
            }}
            h1, h2, h3, h4, h5, h6 {{ 
                color: #2c3e50;
                page-break-after: avoid;
            }}
            h1 {{ 
                border-bottom: 2px solid #3498db; 
                padding-bottom: 10px; 
                color: #1a5276;
                font-size: 24pt;
            }}
            h2 {{ 
                border-bottom: 1px solid #eee; 
                padding-bottom: 5px;
                font-size: 18pt;
                margin-top: 25px;
            }}
            h3 {{ font-size: 14pt; }}
            code {{ 
                background-color: #f5f5f5;
                padding: 2px 5px;
                border-radius: 3px;
                font-family: monospace;
                font-size: 10pt;
            }}
            pre {{ 
                background-color: #f8f8f8;
                padding: 10px;
                border-radius: 5px;
                overflow-x: auto;
                page-break-inside: avoid;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                page-break-inside: avoid;
                font-size: 10pt;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #3498db;
                color: white;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .footer {{
                margin-top: 50px;
                font-size: 9pt;
                text-align: center;
                color: #7f8c8d;
                border-top: 1px solid #eee;
                padding-top: 10px;
            }}
            .page-break {{ 
                page-break-after: always;
            }}
            .no-break {{
                page-break-inside: avoid;
            }}
            .toc a {{
                text-decoration: none;
                color: #3498db;
            }}
            .toc ul {{
                list-style-type: none;
                padding-left: 20px;
            }}
            .toc li {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Guide d'Utilisation ISBISPORTCLUB</h1>
            <p>Version du 08/12/2025</p>
        </div>
        
        <div class="toc">
            <h2>Table des matières</h2>
            <ul>
                <li><a href="#vue-d-ensemble">1. Vue d'ensemble</a></li>
                <li><a href="#installation">2. Installation</a></li>
                <li><a href="#onglet-membres">3. Onglet Membres</a></li>
                <li><a href="#onglet-abonnements">4. Onglet Abonnements</a></li>
                <li><a href="#onglet-paiements">5. Onglet Paiements</a></li>
                <li><a href="#onglet-presences">6. Onglet Présences</a></li>
                <li><a href="#tableau-de-bord">7. Tableau de Bord</a></li>
                <li><a href="#conseils-d-utilisation">8. Conseils d'Utilisation</a></li>
                <li><a href="#maintenance">9. Maintenance</a></li>
            </ul>
        </div>
        
        {}
        
        <div class="footer">
            <p>Document généré le 08/12/2025</p>
            <p>ISBISPORTCLUB - Tous droits réservés © 2025</p>
            <p>Confidentiel - Usage interne uniquement</p>
        </div>
    </body>
    </html>
    """.format(markdown.markdown(md_content, extensions=['tables', 'fenced_code']))
    
    # Écrire le HTML temporaire (optionnel, pour débogage)
    # with open('temp.html', 'w', encoding='utf-8') as f:
    #     f.write(html_content)
    
    # Convertir HTML en PDF
    HTML(string=html_content).write_pdf(pdf_file)

def main():
    # Chemins des fichiers
    base_dir = os.path.dirname(os.path.abspath(__file__))
    md_file = os.path.join(base_dir, 'ISBISPORTCLUB_Documentation', 'README.md')
    pdf_file = os.path.join(base_dir, 'ISBISPORTCLUB_Documentation', 'Guide_Utilisation_ISBISPORTCLUB.pdf')
    
    # Vérifier si le fichier Markdown existe
    if not os.path.exists(md_file):
        print(f"Erreur: Le fichier {md_file} n'existe pas.")
        return
    
    # Créer le PDF
    try:
        convert_md_to_pdf(md_file, pdf_file)
        print(f"PDF généré avec succès : {pdf_file}")
        
        # Créer un fichier ZIP de la documentation
        import shutil
        shutil.make_archive('ISBISPORTCLUB_Documentation', 'zip', 'ISBISPORTCLUB_Documentation')
        print("Archive ZIP créée avec succès : ISBISPORTCLUB_Documentation.zip")
        
    except Exception as e:
        print(f"Une erreur s'est produite lors de la génération du PDF : {str(e)}")

if __name__ == "__main__":
    main()
