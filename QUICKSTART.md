# 🚀 GUIDE DE DÉMARRAGE RAPIDE

## Étape 1: Vérifier Python

Ouvrir PowerShell et taper:
```powershell
python --version
```

Si vous voyez "Python 3.x.x", c'est bon! Sinon, installer depuis:
https://www.python.org/downloads/

## Étape 2: Lancer l'Application

Double-cliquer sur: **start.bat**

OU en ligne de commande:
```powershell
cd C:\Users\nicol\.gemini\antigravity\scratch\ramq-billing-mvp
.\start.bat
```

## Étape 3: Accéder à l'Interface

Deux fenêtres vont s'ouvrir automatiquement:

1. **Documentation API**: http://localhost:8080/docs
2. **Interface Utilisateur**: http://localhost:3000

Si elles ne s'ouvrent pas, ouvrez manuellement ces URLs dans votre navigateur.

## Étape 4: Tester

### Test Automatique
```powershell
python test_api.py
```

### Test Manuel
1. Aller sur http://localhost:3000
2. Remplir le formulaire:
   - Triage: P3
   - Plainte: "Douleur abdominale"
   - Durée: 30 minutes
3. Cliquer "Analyser"
4. Voir les suggestions de codes!

## 🎯 Utilisation Typique

### Scénario: Fin de quart d'urgence

Pour chaque patient:
1. Sélectionner niveau de triage (P1-P5)
2. Entrer plainte principale
3. Cocher procédures effectuées
4. Ajuster durée si nécessaire
5. Cliquer "Analyser"
6. Copier le code suggéré
7. Passer au suivant

**Temps moyen: 30 secondes par cas**

## ⚙️ Configuration Avancée

### Changer le Port Backend
Éditer `backend/app/main.py`, dernière ligne:
```python
uvicorn.run(app, host="0.0.0.0", port=8081)  # Changer 8080 → 8081
```

### Changer le Port Frontend
Éditer `start.bat`, ligne du frontend:
```batch
python -m http.server 3001
```

### Ajouter des Codes RAMQ
Éditer `backend/app/core/init_db.py`, section `sample_codes`

## 🔧 Dépannage

### Problème: "Port déjà utilisé"
**Solution**: Fermer autres applications sur port 8080 ou changer le port

### Problème: "Module not found"
**Solution**:
```powershell
cd backend
pip install -r ..\requirements.txt
```

### Problème: "API non disponible"
**Solution**: Vérifier que la fenêtre backend est ouverte et sans erreurs

### Problème: Page blanche
**Solution**:
1. Ouvrir console navigateur (F12)
2. Vérifier erreurs
3. Vérifier que API répond: http://localhost:8080/health

## 📊 Données Stockées

Toutes les données sont dans:
```
data/
├── ramq.db          # Base de données SQLite
└── usage_*.json     # Usage quotidien (Phase 2)
```

### Backup
Copier le dossier `data/` régulièrement

### Reset
Supprimer `data/ramq.db` et relancer l'application

## 🚀 Prochaines Étapes

### Phase 2: Ajouter ChatGPT (Optionnel)
Coût: ~5-10$/mois pour meilleure précision

```powershell
python upgrade_to_chatgpt.py
```

Puis suivre: `UPGRADE_TO_CHATGPT.txt`

### Phase 3: Déploiement Cloud (Optionnel)
Pour accès depuis n'importe où, voir documentation complète.

## 📞 Besoin d'Aide?

1. Lire le README.md complet
2. Consulter http://localhost:8080/docs
3. Vérifier les logs dans les fenêtres de commande

## ✅ Checklist Première Utilisation

- [ ] Python installé
- [ ] start.bat exécuté
- [ ] http://localhost:8080/health répond "healthy"
- [ ] http://localhost:3000 affiche l'interface
- [ ] Premier cas analysé avec succès
- [ ] Code copié et utilisé

**Tout fonctionne? Vous êtes prêt! 🎉**

---

**Astuce Pro**: Gardez l'application ouverte pendant votre quart.
Analysez vos cas au fur et à mesure pour ne rien oublier!
