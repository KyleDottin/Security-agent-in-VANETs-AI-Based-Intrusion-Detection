Pour lancer le serveur FastAPI

1. Ouvre un terminal dans le dossier du projet

cd C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection\Nassmcp

2. Active l’environnement virtuel

En CMD :
venv\Scripts\activate.bat

3. Lance le serveur FastAPI

uvicorn testnass:app --reload OU  python -m uvicorn testnass:app --reload





🔗 Accès à l'API
API root : http://127.0.0.1:8000

Interface Swagger (documentation interactive) : http://127.0.0.1:8000/docs