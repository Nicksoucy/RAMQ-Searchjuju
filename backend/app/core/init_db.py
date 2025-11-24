"""
Script d'initialisation de la base de données SQLite
Crée le schéma et charge les codes RAMQ initiaux
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def init_database(db_path: str = "data/ramq.db"):
    """Initialise la base de données avec schéma et données"""
    
    # Créer le dossier data si nécessaire
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    
    print(f"🗄️ Initialisation base de données: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Créer tables
    cursor.executescript("""
    -- Table des codes RAMQ
    CREATE TABLE IF NOT EXISTS ramq_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code VARCHAR(10) UNIQUE NOT NULL,
        description TEXT,
        base_fee DECIMAL(10,2),
        category VARCHAR(50),
        modifiers TEXT,
        rules TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Table des encounters (consultations)
    CREATE TABLE IF NOT EXISTS encounters (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        physician_id VARCHAR(50),
        triage_level INTEGER,
        chief_complaint TEXT,
        procedures TEXT,
        duration_minutes INTEGER,
        encounter_datetime TIMESTAMP,
        suggested_codes TEXT,
        selected_code VARCHAR(10),
        total_fee DECIMAL(10,2),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Table de cache IA
    CREATE TABLE IF NOT EXISTS ai_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        input_hash VARCHAR(64) UNIQUE,
        input_data TEXT,
        output_data TEXT,
        model_used VARCHAR(50),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP
    );
    
    -- Index pour performance
    CREATE INDEX IF NOT EXISTS idx_encounters_physician ON encounters(physician_id);
    CREATE INDEX IF NOT EXISTS idx_encounters_date ON encounters(encounter_datetime);
    CREATE INDEX IF NOT EXISTS idx_cache_hash ON ai_cache(input_hash);
    CREATE INDEX IF NOT EXISTS idx_codes_category ON ramq_codes(category);
    """)
    
    print("✅ Schéma créé")
    
    # Insérer codes RAMQ de base
    sample_codes = [
        # Codes d'examen d'urgence
        ("08.48A", "Examen en urgence - Ordinaire", 89.85, "urgence"),
        ("08.48B", "Examen en urgence - Complexe", 134.80, "urgence"),
        ("08.48C", "Examen en urgence - Très complexe", 179.75, "urgence"),
        
        # Codes de consultation d'urgence
        ("08.49A", "Consultation en urgence - Ordinaire", 107.00, "urgence"),
        ("08.49B", "Consultation en urgence - Complexe", 161.00, "urgence"),
        
        # Procédures courantes
        ("15.01", "Suture simple (< 7.5 cm)", 45.00, "procedure"),
        ("15.02", "Suture complexe (> 7.5 cm)", 90.00, "procedure"),
        ("15.03", "Suture face simple", 67.50, "procedure"),
        ("15.04", "Suture face complexe", 135.00, "procedure"),
        ("15.05", "Plâtre membre supérieur", 60.00, "procedure"),
        ("15.06", "Plâtre membre inférieur", 75.00, "procedure"),
        
        # Interprétations
        ("00.44", "Interprétation ECG", 15.00, "interpretation"),
        ("00.45", "Interprétation radiographie", 20.00, "interpretation"),
        
        # Codes spéciaux
        ("08.01", "Visite à domicile", 120.00, "special"),
        ("08.02", "Consultation téléphonique", 35.00, "special"),
        
        # Modificateurs (pour référence)
        ("MOD_NUIT", "Majoration nuit (23h-7h) +30%", 1.3, "modificateur"),
        ("MOD_FDS", "Majoration fin de semaine +20%", 1.2, "modificateur"),
        ("MOD_FERIE", "Majoration jour férié +50%", 1.5, "modificateur"),
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO ramq_codes (code, description, base_fee, category) VALUES (?, ?, ?, ?)",
        sample_codes
    )
    
    conn.commit()
    
    # Vérifier insertion
    cursor.execute("SELECT COUNT(*) FROM ramq_codes")
    count = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"✅ {count} codes RAMQ chargés")
    print(f"✅ Base de données prête: {db_path}")
    
    return db_path

if __name__ == "__main__":
    init_database()
