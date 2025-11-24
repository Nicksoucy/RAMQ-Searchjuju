"""
RAMQ Billing Assistant - Moteur IA Local
Utilise règles déterministes + embeddings pour suggestions de codes
"""

import hashlib
import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import numpy as np

class LocalAIEngine:
    """
    IA locale utilisant règles + embeddings gratuits
    Pas besoin d'API externe - 100% gratuit
    """
    
    def __init__(self, db_path: str = "data/ramq.db"):
        self.db_path = db_path
        self.encoder = None  # Chargé à la demande
        self.codes = []
        self.code_embeddings = None
        
        # Charger codes RAMQ en mémoire
        self.load_ramq_codes()
        
    def load_ramq_codes(self):
        """Charge codes RAMQ depuis la base de données"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT code, description, base_fee, category FROM ramq_codes")
            self.codes = cursor.fetchall()
            
            conn.close()
            print(f"✅ {len(self.codes)} codes RAMQ chargés")
        except Exception as e:
            print(f"⚠️ Erreur chargement codes: {e}")
            self.codes = []
    
    def load_embeddings_model(self):
        """Charge le modèle d'embeddings (une seule fois)"""
        if self.encoder is None:
            try:
                from sentence_transformers import SentenceTransformer
                print("📥 Chargement modèle embeddings local...")
                self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
                
                # Créer embeddings pour tous les codes
                descriptions = [f"{code[1]} {code[3]}" for code in self.codes]
                self.code_embeddings = self.encoder.encode(descriptions)
                print("✅ Modèle embeddings prêt")
            except Exception as e:
                print(f"⚠️ Embeddings non disponibles: {e}")
                self.encoder = None
    
    def analyze_encounter(self, encounter_data: Dict) -> Dict:
        """
        Analyse un cas médical et suggère codes RAMQ
        
        Args:
            encounter_data: Dict avec triage_level, chief_complaint, procedures, etc.
            
        Returns:
            Dict avec suggestions de codes et tarifs
        """
        
        # Vérifier cache d'abord
        cached = self.check_cache(encounter_data)
        if cached:
            cached['from_cache'] = True
            return cached
        
        # Analyse basée sur règles
        suggestions = self.rule_based_analysis(encounter_data)
        
        # Enrichir avec recherche sémantique si disponible
        if encounter_data.get("chief_complaint") and self.encoder:
            semantic_matches = self.semantic_search(
                encounter_data["chief_complaint"],
                encounter_data.get("procedures", [])
            )
            suggestions = self.merge_suggestions(suggestions, semantic_matches)
        
        # Calculer tarifs avec modificateurs
        suggestions = self.apply_modifiers(suggestions, encounter_data)
        
        # Sauvegarder en cache
        self.save_to_cache(encounter_data, suggestions)
        
        suggestions['from_cache'] = False
        return suggestions
    
    def rule_based_analysis(self, data: Dict) -> Dict:
        """
        Analyse par règles déterministes basées sur le guide RAMQ
        """
        
        triage = data.get("triage_level", 3)
        duration = data.get("duration_minutes", 30)
        procedures = data.get("procedures", [])
        
        # Mapping triage -> code de base selon complexité
        base_codes = {
            1: "08.48C",  # P1: Très complexe (réanimation)
            2: "08.48B",  # P2: Complexe (très urgent)
            3: "08.48A",  # P3: Ordinaire (urgent)
            4: "08.48A",  # P4: Ordinaire (moins urgent)
            5: "08.48A"   # P5: Ordinaire (non urgent)
        }
        
        primary_code = base_codes.get(triage, "08.48A")
        
        # Ajuster selon durée (consultation vs examen)
        if duration > 60 and triage <= 2:
            primary_code = "08.49B"  # Consultation complexe
        elif duration > 45 and triage == 3:
            primary_code = "08.49A"  # Consultation ordinaire
        
        # Identifier procédures additionnelles
        procedure_codes = []
        for proc in procedures:
            proc_lower = proc.lower()
            if "suture" in proc_lower:
                if "simple" in proc_lower or len(proc_lower) < 15:
                    procedure_codes.append("15.01")
                else:
                    procedure_codes.append("15.02")
            elif "plâtre" in proc_lower or "platre" in proc_lower:
                if "supérieur" in proc_lower or "bras" in proc_lower:
                    procedure_codes.append("15.05")
                else:
                    procedure_codes.append("15.06")
            elif "ecg" in proc_lower:
                procedure_codes.append("00.44")
        
        return {
            "primary_code": primary_code,
            "procedure_codes": procedure_codes,
            "confidence": 0.85,
            "reasoning": f"Basé sur triage P{triage}, durée {duration}min"
        }
    
    def semantic_search(self, complaint: str, procedures: List[str]) -> List[Dict]:
        """
        Recherche sémantique dans les codes RAMQ
        Utilise embeddings pour trouver codes similaires
        """
        
        if not self.encoder or self.code_embeddings is None:
            return []
        
        try:
            # Créer embedding de la requête
            query = f"{complaint} {' '.join(procedures)}"
            query_embedding = self.encoder.encode([query])[0]
            
            # Calculer similarités cosinus
            similarities = np.dot(self.code_embeddings, query_embedding)
            top_indices = np.argsort(similarities)[-5:][::-1]
            
            matches = []
            for idx in top_indices:
                code = self.codes[idx]
                matches.append({
                    "code": code[0],
                    "description": code[1],
                    "base_fee": code[2],
                    "similarity": float(similarities[idx])
                })
            
            return matches
        except Exception as e:
            print(f"⚠️ Erreur recherche sémantique: {e}")
            return []
    
    def merge_suggestions(self, rule_based: Dict, semantic: List[Dict]) -> Dict:
        """Fusionne suggestions basées sur règles et recherche sémantique"""
        
        # Pour l'instant, on garde les règles comme base
        # et on ajoute les matches sémantiques comme alternatives
        rule_based['semantic_alternatives'] = semantic[:3]
        
        return rule_based
    
    def apply_modifiers(self, suggestions: Dict, data: Dict) -> Dict:
        """
        Applique modificateurs tarifaires selon contexte
        - Nuit (23h-7h): +30%
        - Fin de semaine: +20%
        - Jour férié: +50%
        """
        
        encounter_time = data.get("encounter_datetime")
        if isinstance(encounter_time, str):
            encounter_time = datetime.fromisoformat(encounter_time)
        elif encounter_time is None:
            encounter_time = datetime.now()
        
        modifiers = []
        multiplier = 1.0
        
        # Vérifier nuit (23h-7h)
        if encounter_time.hour >= 23 or encounter_time.hour < 7:
            modifiers.append("NUIT")
            multiplier *= 1.3
        
        # Vérifier fin de semaine (samedi=5, dimanche=6)
        if encounter_time.weekday() >= 5:
            modifiers.append("FDS")
            multiplier *= 1.2
        
        # Vérifier jour férié (liste simplifiée 2024-2025)
        if self.is_holiday(encounter_time):
            modifiers.append("FÉRIÉ")
            multiplier *= 1.5
        
        # Calculer tarif total
        base_fee = self.get_base_fee(suggestions["primary_code"])
        total_fee = base_fee * multiplier
        
        # Ajouter frais procédures
        procedure_fees = []
        for proc_code in suggestions.get("procedure_codes", []):
            proc_fee = self.get_base_fee(proc_code)
            procedure_fees.append({"code": proc_code, "fee": proc_fee})
            total_fee += proc_fee
        
        suggestions["modifiers"] = modifiers
        suggestions["multiplier"] = round(multiplier, 2)
        suggestions["base_fee"] = base_fee
        suggestions["procedure_fees"] = procedure_fees
        suggestions["total_fee"] = round(total_fee, 2)
        
        return suggestions
    
    def get_base_fee(self, code: str) -> float:
        """Récupère le tarif de base d'un code RAMQ"""
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT base_fee FROM ramq_codes WHERE code = ?", (code,))
            result = cursor.fetchone()
            
            conn.close()
            
            return float(result[0]) if result else 0.0
        except Exception as e:
            print(f"⚠️ Erreur récupération tarif: {e}")
            return 0.0
    
    def is_holiday(self, date: datetime) -> bool:
        """Vérifie si la date est un jour férié au Québec"""
        
        # Jours fériés fixes 2024-2025
        holidays = [
            '2024-01-01', '2024-04-01', '2024-05-20', '2024-06-24', 
            '2024-07-01', '2024-09-02', '2024-10-14', '2024-12-25', '2024-12-26',
            '2025-01-01', '2025-04-18', '2025-05-19', '2025-06-24',
            '2025-07-01', '2025-09-01', '2025-10-13', '2025-12-25', '2025-12-26'
        ]
        
        date_str = date.strftime('%Y-%m-%d')
        return date_str in holidays
    
    def check_cache(self, data: Dict) -> Optional[Dict]:
        """Vérifie si un résultat similaire existe en cache"""
        
        try:
            # Créer hash de l'input (sans datetime pour plus de hits)
            cache_data = {
                'triage': data.get('triage_level'),
                'complaint': data.get('chief_complaint', '')[:50],
                'procedures': sorted(data.get('procedures', []))
            }
            cache_key = hashlib.md5(
                json.dumps(cache_data, sort_keys=True).encode()
            ).hexdigest()
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT output_data FROM ai_cache 
                WHERE input_hash = ? AND expires_at > ?
            """, (cache_key, datetime.now()))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result[0])
            
        except Exception as e:
            print(f"⚠️ Erreur cache: {e}")
        
        return None
    
    def save_to_cache(self, input_data: Dict, output_data: Dict):
        """Sauvegarde résultat en cache pour 7 jours"""
        
        try:
            cache_data = {
                'triage': input_data.get('triage_level'),
                'complaint': input_data.get('chief_complaint', '')[:50],
                'procedures': sorted(input_data.get('procedures', []))
            }
            cache_key = hashlib.md5(
                json.dumps(cache_data, sort_keys=True).encode()
            ).hexdigest()
            
            expires = datetime.now() + timedelta(days=7)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO ai_cache 
                (input_hash, input_data, output_data, model_used, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                cache_key,
                json.dumps(input_data),
                json.dumps(output_data),
                "local_rules_v1",
                expires
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Erreur sauvegarde cache: {e}")
