"""
Script d'upgrade vers ChatGPT API (Phase 2)
Ajoute l'intégration ChatGPT avec fallback sur moteur local
Coût estimé: 5-10$/mois
"""

import os
from pathlib import Path

def create_hybrid_engine():
    """Crée le moteur IA hybride avec ChatGPT + fallback local"""
    
    hybrid_code = '''"""
RAMQ Billing Assistant - Moteur IA Hybride
Utilise ChatGPT API avec fallback sur règles locales
"""

import os
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
import asyncio

# Import moteur local comme fallback
from app.core.ai_local import LocalAIEngine

class HybridAIEngine:
    """
    Moteur IA hybride: ChatGPT en priorité, fallback local
    """
    
    def __init__(self, db_path: str = "data/ramq.db"):
        self.db_path = db_path
        
        # Vérifier si clé OpenAI disponible
        self.openai_key = os.getenv("OPENAI_API_KEY")
        
        if self.openai_key:
            try:
                import openai
                openai.api_key = self.openai_key
                self.openai = openai
                self.mode = "hybrid"
                print("✅ Mode hybride activé (ChatGPT + Local)")
            except ImportError:
                print("⚠️ Package openai non installé, mode local uniquement")
                self.mode = "local"
                self.openai = None
        else:
            print("ℹ️ Pas de clé OpenAI, mode local uniquement")
            self.mode = "local"
            self.openai = None
        
        # Initialiser moteur local (toujours disponible)
        self.local_engine = LocalAIEngine(db_path)
        
        # Compteurs pour budget
        self.daily_budget = float(os.getenv("DAILY_API_BUDGET", "5.0"))
        self.usage_today = 0.0
    
    async def analyze_encounter(self, encounter_data: Dict) -> Dict:
        """
        Analyse avec ChatGPT si disponible, sinon fallback local
        """
        
        # Toujours vérifier cache d'abord
        cached = self.local_engine.check_cache(encounter_data)
        if cached:
            cached['from_cache'] = True
            cached['model_used'] = 'cache'
            return cached
        
        # Essayer ChatGPT si mode hybride et budget disponible
        if self.mode == "hybrid" and self.can_use_chatgpt():
            try:
                result = await self.analyze_with_chatgpt(encounter_data)
                result['model_used'] = 'chatgpt'
                
                # Sauvegarder en cache
                self.local_engine.save_to_cache(encounter_data, result)
                
                return result
                
            except Exception as e:
                print(f"⚠️ Erreur ChatGPT, fallback local: {e}")
                # Continuer avec moteur local
        
        # Fallback: moteur local
        result = self.local_engine.analyze_encounter(encounter_data)
        result['model_used'] = 'local'
        return result
    
    def can_use_chatgpt(self) -> bool:
        """Vérifie si on peut utiliser ChatGPT selon budget"""
        
        # Vérifier usage du jour
        today = datetime.now().strftime('%Y-%m-%d')
        usage_file = Path(f"data/usage_{today}.json")
        
        if usage_file.exists():
            with open(usage_file, 'r') as f:
                data = json.load(f)
                self.usage_today = data.get('total_cost', 0.0)
        
        return self.usage_today < self.daily_budget
    
    async def analyze_with_chatgpt(self, data: Dict) -> Dict:
        """
        Analyse avec ChatGPT API
        Utilise prompt optimisé pour minimiser tokens
        """
        
        # Construire prompt concis
        prompt = self.build_chatgpt_prompt(data)
        
        # Appel API
        response = await self.openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",  # Ou gpt-4o-mini pour encore moins cher
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un expert en facturation RAMQ pour urgences au Québec. Réponds en JSON uniquement."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0,
            max_tokens=200,
            response_format={"type": "json_object"}
        )
        
        # Parser réponse
        result_text = response.choices[0].message.content
        result = json.loads(result_text)
        
        # Tracker coût
        tokens_used = response.usage.total_tokens
        cost = self.calculate_cost(tokens_used, "gpt-3.5-turbo")
        self.track_usage(cost)
        
        # Enrichir avec calculs locaux (modificateurs, etc.)
        result = self.local_engine.apply_modifiers(result, data)
        result['chatgpt_cost'] = cost
        result['confidence'] = 0.95  # ChatGPT plus précis
        
        return result
    
    def build_chatgpt_prompt(self, data: Dict) -> str:
        """Construit prompt optimisé (minimal tokens)"""
        
        return f"""Cas urgence:
- Triage: P{data.get('triage_level')}
- Plainte: {data.get('chief_complaint', '')[:50]}
- Procédures: {', '.join(data.get('procedures', [])[:3])}
- Durée: {data.get('duration_minutes')}min

Retourne JSON:
{{
  "primary_code": "XX.XXX",
  "procedure_codes": ["XX.XX"],
  "reasoning": "justification courte"
}}"""
    
    def calculate_cost(self, tokens: int, model: str) -> float:
        """Calcule coût en USD"""
        
        pricing = {
            "gpt-3.5-turbo": 0.0015 / 1000,  # $0.0015 per 1K tokens
            "gpt-4o-mini": 0.00015 / 1000     # $0.00015 per 1K tokens
        }
        
        return tokens * pricing.get(model, 0.002)
    
    def track_usage(self, cost: float):
        """Enregistre usage quotidien"""
        
        today = datetime.now().strftime('%Y-%m-%d')
        usage_file = Path(f"data/usage_{today}.json")
        
        if usage_file.exists():
            with open(usage_file, 'r') as f:
                data = json.load(f)
        else:
            data = {'date': today, 'total_cost': 0.0, 'calls': 0}
        
        data['total_cost'] += cost
        data['calls'] += 1
        self.usage_today = data['total_cost']
        
        with open(usage_file, 'w') as f:
            json.dump(data, f, indent=2)
'''
    
    # Sauvegarder fichier
    output_path = Path("backend/app/core/ai_hybrid.py")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(hybrid_code)
    
    print(f"✅ Moteur hybride créé: {output_path}")
    return output_path

def update_main_api():
    """Met à jour main.py pour utiliser moteur hybride"""
    
    print("📝 Mise à jour de l'API pour mode hybride...")
    
    # Instructions pour l'utilisateur
    instructions = """
# INSTRUCTIONS POUR ACTIVER CHATGPT
# ==================================

1. Installer le package OpenAI:
   pip install openai

2. Obtenir clé API OpenAI:
   - Aller sur https://platform.openai.com/api-keys
   - Créer une nouvelle clé API
   - Copier la clé (commence par sk-...)

3. Configurer la clé:
   # Créer fichier .env à la racine du projet
   OPENAI_API_KEY=sk-votre-cle-ici
   DAILY_API_BUDGET=5.0

4. Modifier backend/app/main.py:
   # Ligne 12, remplacer:
   from app.core.ai_local import LocalAIEngine
   # Par:
   from app.core.ai_hybrid import HybridAIEngine as LocalAIEngine

5. Redémarrer l'application:
   start.bat

Le système utilisera automatiquement ChatGPT quand disponible,
avec fallback sur moteur local si:
- Budget quotidien atteint
- Erreur API
- Pas de connexion internet

Coût estimé: 5-10$/mois pour usage normal
"""
    
    instructions_path = Path("UPGRADE_TO_CHATGPT.txt")
    with open(instructions_path, 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    print(f"✅ Instructions créées: {instructions_path}")
    return instructions_path

def create_requirements_upgrade():
    """Crée requirements pour Phase 2"""
    
    requirements = """# Phase 2: Ajout ChatGPT
openai==1.6.1
python-dotenv==1.0.0
"""
    
    path = Path("requirements-phase2.txt")
    with open(path, 'w') as f:
        f.write(requirements)
    
    print(f"✅ Requirements Phase 2: {path}")
    return path

if __name__ == "__main__":
    print("🚀 Upgrade vers ChatGPT (Phase 2)")
    print("=" * 50)
    
    # Créer fichiers
    create_hybrid_engine()
    update_main_api()
    create_requirements_upgrade()
    
    print("\n" + "=" * 50)
    print("✅ Upgrade préparé!")
    print("\nLire: UPGRADE_TO_CHATGPT.txt pour instructions")
    print("\nCoût estimé après activation: 5-10$/mois")
