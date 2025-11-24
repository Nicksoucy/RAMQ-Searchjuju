"""
RAMQ Billing Assistant - API FastAPI
Version locale avec moteur IA intégré
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime
import os
import sys
from pathlib import Path

# Ajouter le chemin pour imports
sys.path.append(str(Path(__file__).parent.parent))

from app.core.ai_local import LocalAIEngine
from app.core.init_db import init_database

# Initialisation
app = FastAPI(
    title="RAMQ Billing Assistant API",
    version="1.0.0",
    description="Assistant IA pour facturation RAMQ - Version Locale"
)

# CORS pour frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production: spécifier domaines exacts
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser base de données au démarrage
@app.on_event("startup")
async def startup_event():
    """Initialisation au démarrage"""
    print("🚀 Démarrage RAMQ Billing Assistant API")
    
    # Créer DB si elle n'existe pas
    db_path = "data/ramq.db"
    if not Path(db_path).exists():
        print("📦 Première exécution - Initialisation base de données...")
        init_database(db_path)
    
    # Initialiser moteur IA
    global ai_engine
    ai_engine = LocalAIEngine(db_path)
    print("✅ Moteur IA local prêt")

# Modèles Pydantic
class EncounterRequest(BaseModel):
    """Requête d'analyse d'un cas médical"""
    triage_level: int = Field(..., ge=1, le=5, description="Niveau de triage (1-5)")
    chief_complaint: str = Field(..., max_length=500, description="Plainte principale")
    procedures: List[str] = Field(default_factory=list, description="Procédures effectuées")
    duration_minutes: int = Field(..., ge=1, le=480, description="Durée en minutes")
    encounter_datetime: Optional[str] = Field(default=None, description="Date/heure ISO format")
    
    class Config:
        json_schema_extra = {
            "example": {
                "triage_level": 2,
                "chief_complaint": "Douleur thoracique atypique",
                "procedures": ["ECG", "Enzymes cardiaques"],
                "duration_minutes": 75,
                "encounter_datetime": "2024-11-24T23:30:00"
            }
        }

class BillingResponse(BaseModel):
    """Réponse avec suggestions de facturation"""
    primary_code: str
    procedure_codes: List[str]
    modifiers: List[str]
    total_fee: float
    base_fee: float
    confidence: float
    details: Dict
    from_cache: bool = False

# Routes API
@app.get("/")
async def root():
    """Page d'accueil de l'API"""
    return {
        "message": "RAMQ Billing Assistant API",
        "version": "1.0.0",
        "status": "operational",
        "mode": "local",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Vérification santé de l'API"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "ai_engine": "local_rules_v1"
    }

@app.post("/api/analyze", response_model=BillingResponse)
async def analyze_encounter(request: EncounterRequest):
    """
    Analyse un encounter et retourne suggestions de facturation
    
    - **triage_level**: 1 (réanimation) à 5 (non urgent)
    - **chief_complaint**: Raison de consultation
    - **procedures**: Liste des procédures effectuées
    - **duration_minutes**: Durée de la consultation
    - **encounter_datetime**: Date/heure (optionnel, défaut = maintenant)
    """
    try:
        # Convertir en dict pour traitement
        encounter_data = request.dict()
        
        # Analyser avec moteur IA
        result = ai_engine.analyze_encounter(encounter_data)
        
        # Formater réponse
        response = BillingResponse(
            primary_code=result.get("primary_code", ""),
            procedure_codes=result.get("procedure_codes", []),
            modifiers=result.get("modifiers", []),
            total_fee=result.get("total_fee", 0.0),
            base_fee=result.get("base_fee", 0.0),
            confidence=result.get("confidence", 0.0),
            details=result,
            from_cache=result.get("from_cache", False)
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur analyse: {str(e)}")

@app.get("/api/codes")
async def get_codes(category: Optional[str] = None, search: Optional[str] = None):
    """
    Récupère liste des codes RAMQ
    
    - **category**: Filtrer par catégorie (urgence, procedure, interpretation)
    - **search**: Recherche dans description
    """
    import sqlite3
    from pathlib import Path
    
    try:
        # Utiliser le chemin correct de la base de données
        db_path = Path(__file__).parent.parent / "data" / "ramq.db"
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        if category:
            cursor.execute(
                "SELECT code, description, base_fee, category FROM ramq_codes WHERE category = ?",
                (category,)
            )
        elif search:
            cursor.execute(
                "SELECT code, description, base_fee, category FROM ramq_codes WHERE description LIKE ? OR code LIKE ?",
                (f"%{search}%", f"%{search}%")
            )
        else:
            cursor.execute("SELECT code, description, base_fee, category FROM ramq_codes")
        
        codes = [
            {
                "code": row[0],
                "description": row[1],
                "base_fee": row[2],
                "category": row[3]
            }
            for row in cursor.fetchall()
        ]
        
        conn.close()
        
        return {"codes": codes, "count": len(codes)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération codes: {str(e)}")

@app.get("/api/statistics")
async def get_statistics():
    """
    Statistiques d'utilisation
    """
    import sqlite3
    
    try:
        conn = sqlite3.connect("data/ramq.db")
        cursor = conn.cursor()
        
        # Stats basiques
        cursor.execute("SELECT COUNT(*) FROM encounters")
        total_encounters = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(total_fee) FROM encounters WHERE total_fee IS NOT NULL")
        avg_fee = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT COUNT(DISTINCT physician_id) FROM encounters")
        total_physicians = cursor.fetchone()[0]
        
        # Cache stats
        cursor.execute("SELECT COUNT(*) FROM ai_cache WHERE expires_at > ?", (datetime.now(),))
        cache_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_encounters": total_encounters,
            "average_fee": round(avg_fee, 2),
            "total_physicians": total_physicians,
            "cache_entries": cache_entries,
            "ai_model": "local_rules_v1",
            "cost": "0$ (100% local)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur statistiques: {str(e)}")

@app.post("/api/save-encounter")
async def save_encounter(
    encounter: EncounterRequest,
    selected_code: str,
    total_fee: float,
    physician_id: str = "default"
):
    """
    Sauvegarde un encounter pour historique
    """
    import sqlite3
    import json
    
    try:
        conn = sqlite3.connect("data/ramq.db")
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO encounters 
            (physician_id, triage_level, chief_complaint, procedures, duration_minutes,
             encounter_datetime, selected_code, total_fee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            physician_id,
            encounter.triage_level,
            encounter.chief_complaint,
            json.dumps(encounter.procedures),
            encounter.duration_minutes,
            encounter.encounter_datetime or datetime.now().isoformat(),
            selected_code,
            total_fee
        ))
        
        conn.commit()
        encounter_id = cursor.lastrowid
        conn.close()
        
        return {
            "success": True,
            "encounter_id": encounter_id,
            "message": "Encounter sauvegardé"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur sauvegarde: {str(e)}")

# Lancement direct
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
