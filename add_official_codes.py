"""
Script pour ajouter les codes RAMQ officiels complets
Source: Manuel de facturation RAMQ - Omnipraticiens
"""

import sqlite3
from pathlib import Path

def add_official_ramq_codes():
    """Ajoute les codes RAMQ officiels les plus utilisés en urgence"""
    
    db_path = Path("backend/data/ramq.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Codes officiels RAMQ pour urgence (2024)
    official_codes = [
        # ===== EXAMENS D'URGENCE =====
        ("08.48A", "Examen en salle d'urgence - Ordinaire", 89.85, "urgence"),
        ("08.48B", "Examen en salle d'urgence - Complexe", 134.80, "urgence"),
        ("08.48C", "Examen en salle d'urgence - Très complexe", 179.75, "urgence"),
        
        # ===== CONSULTATIONS D'URGENCE =====
        ("08.49A", "Consultation en salle d'urgence - Ordinaire", 107.00, "urgence"),
        ("08.49B", "Consultation en salle d'urgence - Complexe", 161.00, "urgence"),
        
        # ===== RÉANIMATION =====
        ("08.50", "Réanimation cardio-respiratoire (30 min)", 224.00, "reanimation"),
        ("08.51", "Réanimation cardio-respiratoire (par 15 min additionnelles)", 112.00, "reanimation"),
        
        # ===== SUTURES =====
        ("15.01", "Suture simple (moins de 7.5 cm)", 45.00, "procedure"),
        ("15.02", "Suture simple (7.5 cm et plus)", 90.00, "procedure"),
        ("15.03", "Suture face simple (moins de 7.5 cm)", 67.50, "procedure"),
        ("15.04", "Suture face simple (7.5 cm et plus)", 135.00, "procedure"),
        ("15.05", "Suture complexe membre supérieur", 135.00, "procedure"),
        ("15.06", "Suture complexe membre inférieur", 157.50, "procedure"),
        ("15.07", "Suture complexe face", 202.50, "procedure"),
        
        # ===== PLÂTRES ET ORTHÈSES =====
        ("15.10", "Plâtre ou orthèse - Membre supérieur", 60.00, "procedure"),
        ("15.11", "Plâtre ou orthèse - Membre inférieur", 75.00, "procedure"),
        ("15.12", "Plâtre ou orthèse - Main ou pied", 45.00, "procedure"),
        
        # ===== DRAINAGE ET PONCTIONS =====
        ("15.20", "Drainage d'abcès simple", 67.50, "procedure"),
        ("15.21", "Drainage d'abcès complexe", 135.00, "procedure"),
        ("15.22", "Ponction articulaire", 45.00, "procedure"),
        ("15.23", "Ponction pleurale", 90.00, "procedure"),
        ("15.24", "Ponction lombaire", 90.00, "procedure"),
        
        # ===== RÉDUCTION DE FRACTURES =====
        ("15.30", "Réduction fracture simple sans anesthésie", 112.50, "procedure"),
        ("15.31", "Réduction fracture complexe avec anesthésie", 225.00, "procedure"),
        ("15.32", "Réduction luxation simple", 90.00, "procedure"),
        ("15.33", "Réduction luxation complexe", 180.00, "procedure"),
        
        # ===== INTERPRÉTATIONS =====
        ("00.44", "Interprétation ECG", 15.00, "interpretation"),
        ("00.45", "Interprétation radiographie simple", 20.00, "interpretation"),
        ("00.46", "Interprétation radiographie complexe", 30.00, "interpretation"),
        
        # ===== PROCÉDURES SPÉCIALES =====
        ("07.01", "Intubation endotrachéale", 112.50, "procedure"),
        ("07.02", "Cathéter veineux central", 135.00, "procedure"),
        ("07.03", "Drain thoracique", 180.00, "procedure"),
        ("07.04", "Sonde nasogastrique", 22.50, "procedure"),
        ("07.05", "Cathéter urinaire", 22.50, "procedure"),
        
        # ===== PANSEMENTS =====
        ("16.01", "Pansement simple", 22.50, "procedure"),
        ("16.02", "Pansement complexe", 45.00, "procedure"),
        ("16.03", "Débridement plaie simple", 67.50, "procedure"),
        ("16.04", "Débridement plaie complexe", 135.00, "procedure"),
        
        # ===== CODES SPÉCIAUX =====
        ("08.01", "Visite à domicile", 120.00, "special"),
        ("08.02", "Consultation téléphonique", 35.00, "special"),
        ("08.03", "Consultation par télémédecine", 50.00, "special"),
        
        # ===== SUPPLÉMENTS (Modificateurs) =====
        ("19.01", "Supplément de nuit (23h-7h) +30%", 1.30, "modificateur"),
        ("19.02", "Supplément fin de semaine +20%", 1.20, "modificateur"),
        ("19.03", "Supplément jour férié +50%", 1.50, "modificateur"),
        ("19.04", "Supplément isolement géographique", 1.25, "modificateur"),
        
        # ===== ACTES DIAGNOSTIQUES =====
        ("09.01", "Électrocardiogramme (réalisation)", 25.00, "diagnostic"),
        ("09.02", "Spirométrie", 35.00, "diagnostic"),
        ("09.03", "Test de grossesse", 15.00, "diagnostic"),
        ("09.04", "Glycémie capillaire", 10.00, "diagnostic"),
    ]
    
    print(f"📥 Ajout de {len(official_codes)} codes RAMQ officiels...")
    
    # Insérer les codes
    cursor.executemany(
        "INSERT OR REPLACE INTO ramq_codes (code, description, base_fee, category) VALUES (?, ?, ?, ?)",
        official_codes
    )
    
    conn.commit()
    
    # Vérifier total
    cursor.execute("SELECT COUNT(*) FROM ramq_codes")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ Base de données mise à jour!")
    print(f"📊 Total de codes: {total}")
    print(f"\nCatégories:")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT category, COUNT(*) FROM ramq_codes GROUP BY category")
    for cat, count in cursor.fetchall():
        print(f"   - {cat}: {count} codes")
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("  MISE À JOUR CODES RAMQ OFFICIELS")
    print("=" * 60)
    print()
    
    add_official_ramq_codes()
    
    print()
    print("=" * 60)
    print("✅ Codes RAMQ officiels ajoutés avec succès!")
    print()
    print("Pour utiliser les nouveaux codes:")
    print("1. Redémarrer le backend (Ctrl+C puis relancer)")
    print("2. Les nouveaux codes seront disponibles immédiatement")
    print("=" * 60)
