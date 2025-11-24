import pandas as pd
import sqlite3
import os
from pathlib import Path

def import_data():
    db_path = Path('backend/data/ramq.db')
    excel_path = Path('backend/data/ramq_full.xlsx')
    
    if not excel_path.exists():
        print(f"❌ Fichier Excel non trouvé: {excel_path}")
        return

    print(f"📂 Lecture du fichier Excel: {excel_path}")
    
    try:
        # Lire toutes les feuilles
        xls = pd.ExcelFile(excel_path)
        print(f"📑 Feuilles trouvées: {xls.sheet_names}")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Vider la table actuelle (ou on pourrait merger, mais pour l'instant on remplace pour être propre)
        # On garde la structure mais on vide les données
        cursor.execute("DELETE FROM ramq_codes")
        print("🗑️  Anciennes données effacées")
        
        total_imported = 0
        
        # Mapping des colonnes (adapté selon la structure probable générée par Claude)
        # On va essayer de détecter les colonnes intelligemment
        
        for sheet_name in xls.sheet_names:
            if sheet_name in ['Guide_Rapide', 'References_Ressources', 'Optimisation_Facturation']:
                continue # On saute les feuilles qui ne sont pas des codes purs pour l'instant
                
            df = pd.read_excel(xls, sheet_name=sheet_name)
            print(f"  Traitement feuille: {sheet_name} ({len(df)} lignes)")
            
            # Standardisation des noms de colonnes
            df.columns = [str(c).upper().strip() for c in df.columns]
            
            for _, row in df.iterrows():
                try:
                    # Essayer de trouver les colonnes correspondantes
                    code = None
                    desc = None
                    price = 0.0
                    keywords = ""
                    
                    # Logique de recherche de colonnes
                    for col in df.columns:
                        if 'CODE' in col:
                            code = str(row[col]).strip()
                        elif 'DESCRIPTION' in col or 'LIBELLÉ' in col or 'ACTE' in col:
                            desc = str(row[col]).strip()
                        elif 'PRIX' in col or 'TARIF' in col or 'MONTANT' in col:
                            try:
                                val = str(row[col]).replace('$', '').replace(',', '.').strip()
                                price = float(val) if val and val != 'nan' else 0.0
                            except:
                                price = 0.0
                        elif 'MOTS' in col or 'KEYWORD' in col or 'CONTEXTE' in col:
                            keywords = str(row[col]).strip() if str(row[col]) != 'nan' else ""

                    # Si on a au moins un code et une description
                    if code and desc and code != 'nan' and desc != 'nan':
                        # Enrichir la description avec les mots-clés pour la recherche
                        full_desc = desc
                        if keywords:
                            full_desc += f" | {keywords}"
                        
                        # Ajouter la catégorie basée sur le nom de la feuille
                        category = sheet_name.replace('_', ' ').lower()
                        
                        cursor.execute("""
                            INSERT OR REPLACE INTO ramq_codes (code, description, base_fee, category)
                            VALUES (?, ?, ?, ?)
                        """, (code, full_desc, price, category))
                        
                        total_imported += 1
                        
                except Exception as e:
                    print(f"⚠️ Erreur ligne: {e}")
                    continue
                    
        conn.commit()
        conn.close()
        print(f"\n✅ Importation terminée ! {total_imported} codes importés.")
        
    except Exception as e:
        print(f"❌ Erreur critique: {e}")

if __name__ == "__main__":
    import_data()
