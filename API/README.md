Pour lancer le serveur FastAPI

1. Ouvre un terminal dans le dossier du projet

cd C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Nassmcp

2. Active l’environnement virtuel

En CMD :
venv\Scripts\activate.bat

# Démarrage du serveur FastAPI pour l'API
## 1. Ouvrir un terminal dans le dossier du projet
```sh
cd C:\Users\tru89\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\API
```
## 2. Activer l’environnement virtuel
En CMD :
```sh
venv\Scripts\activate.bat
```
En PowerShell :
```sh
.\venv\Scripts\Activate.ps1
```
## 3. Lancer le serveur FastAPI
```sh
uvicorn main:app --reload
# ou
python -m uvicorn main:app --reload
```
---
## 🔗 Accès à l'API
- Racine de l'API : [http://127.0.0.1:8000](http://127.0.0.1:8000)
- Documentation interactive Swagger : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
---
**Remarques :**
- Assurez-vous d'être dans le bon dossier (`API`) avant de lancer les commandes.
- Vérifiez que le fichier `main.py` existe dans ce dossier.
- L'environnement virtuel doit être activé à chaque nouvelle session de terminal.