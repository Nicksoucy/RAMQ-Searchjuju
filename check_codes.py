import sqlite3

def check_codes():
    try:
        conn = sqlite3.connect('backend/data/ramq.db')
        cursor = conn.cursor()
        
        keywords = ['trauma', 'coeur', 'cardiaque', 'blessure', 'plaie']
        print(f"Recherche des codes contenant: {', '.join(keywords)}\n")
        
        for keyword in keywords:
            cursor.execute("SELECT code, description, base_fee FROM ramq_codes WHERE description LIKE ?", (f'%{keyword}%',))
            results = cursor.fetchall()
            if results:
                print(f"--- Résultats pour '{keyword}' ---")
                for row in results:
                    print(f"[{row[0]}] {row[1]} ({row[2]}$)")
            else:
                print(f"--- Aucun résultat pour '{keyword}' ---")
            print("")
            
        conn.close()
    except Exception as e:
        print(f"Erreur: {e}")

if __name__ == "__main__":
    check_codes()
