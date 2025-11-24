"""
Script de test pour vérifier l'API RAMQ Billing
"""

import requests
import json
from datetime import datetime

API_URL = "http://localhost:8080"

def test_health():
    """Test endpoint health"""
    print("🔍 Test 1: Health Check...")
    try:
        response = requests.get(f"{API_URL}/health")
        if response.status_code == 200:
            print("✅ API en ligne:", response.json())
            return True
        else:
            print("❌ API erreur:", response.status_code)
            return False
    except Exception as e:
        print(f"❌ Impossible de se connecter à l'API: {e}")
        print("   Assurez-vous que le backend est démarré (start.bat)")
        return False

def test_analyze_simple():
    """Test analyse cas simple"""
    print("\n🔍 Test 2: Analyse cas simple (P3, 30min)...")
    
    data = {
        "triage_level": 3,
        "chief_complaint": "Douleur abdominale",
        "procedures": [],
        "duration_minutes": 30,
        "encounter_datetime": datetime.now().isoformat()
    }
    
    try:
        response = requests.post(f"{API_URL}/api/analyze", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Code suggéré: {result['primary_code']}")
            print(f"   Tarif: {result['total_fee']}$")
            print(f"   Confiance: {result['confidence']*100}%")
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_analyze_complex():
    """Test analyse cas complexe avec procédures"""
    print("\n🔍 Test 3: Analyse cas complexe (P2, suture, nuit)...")
    
    # Cas de nuit (23h30)
    night_time = datetime.now().replace(hour=23, minute=30)
    
    data = {
        "triage_level": 2,
        "chief_complaint": "Lacération profonde avant-bras",
        "procedures": ["Suture complexe", "Radiographie"],
        "duration_minutes": 75,
        "encounter_datetime": night_time.isoformat()
    }
    
    try:
        response = requests.post(f"{API_URL}/api/analyze", json=data)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Code principal: {result['primary_code']}")
            print(f"   Procédures: {result['procedure_codes']}")
            print(f"   Modificateurs: {result['modifiers']}")
            print(f"   Tarif total: {result['total_fee']}$")
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_get_codes():
    """Test récupération codes RAMQ"""
    print("\n🔍 Test 4: Récupération codes RAMQ...")
    
    try:
        response = requests.get(f"{API_URL}/api/codes?category=urgence")
        if response.status_code == 200:
            result = response.json()
            print(f"✅ {result['count']} codes trouvés")
            if result['codes']:
                print(f"   Exemple: {result['codes'][0]['code']} - {result['codes'][0]['description']}")
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def test_statistics():
    """Test statistiques"""
    print("\n🔍 Test 5: Statistiques...")
    
    try:
        response = requests.get(f"{API_URL}/api/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Statistiques:")
            print(f"   Cas analysés: {stats['total_encounters']}")
            print(f"   Tarif moyen: {stats['average_fee']}$")
            print(f"   Modèle IA: {stats['ai_model']}")
            print(f"   Coût: {stats['cost']}")
            return True
        else:
            print(f"❌ Erreur: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

def run_all_tests():
    """Exécute tous les tests"""
    print("=" * 60)
    print("  TESTS API RAMQ BILLING ASSISTANT")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health
    results.append(("Health Check", test_health()))
    
    if not results[0][1]:
        print("\n❌ API non disponible. Arrêt des tests.")
        print("   Lancez d'abord: start.bat")
        return
    
    # Tests suivants
    results.append(("Analyse Simple", test_analyze_simple()))
    results.append(("Analyse Complexe", test_analyze_complex()))
    results.append(("Codes RAMQ", test_get_codes()))
    results.append(("Statistiques", test_statistics()))
    
    # Résumé
    print("\n" + "=" * 60)
    print("  RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nRésultat: {passed}/{total} tests réussis")
    
    if passed == total:
        print("\n🎉 Tous les tests sont passés!")
        print("   L'application est prête à l'emploi.")
        print("   Ouvrez: http://localhost:3000")
    else:
        print("\n⚠️ Certains tests ont échoué.")
        print("   Vérifiez les erreurs ci-dessus.")

if __name__ == "__main__":
    run_all_tests()
