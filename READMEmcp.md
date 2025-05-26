🚀 Lancer le serveur FastAPI
1. Ouvre un terminal dans le dossier du projet
powershell
Copier
Modifier
cd C:\Users\nanem\Security-agent-in-VANETs-AI-Based-Intrusion-Detection
2. Active l’environnement virtuel
✅ En PowerShell :
powershell
Copier
Modifier
.\venv\Scripts\activate
💡 Si tu obtiens une erreur liée à l’exécution des scripts, exécute d'abord :

powershell
Copier
Modifier
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
✅ Ou en CMD :
cmd
Copier
Modifier
venv\Scripts\activate.bat
3. Lance le serveur FastAPI
bash
Copier
Modifier
uvicorn testnass:app --reload
🔗 Accès à l'API
API root : http://127.0.0.1:8000

Interface Swagger (documentation interactive) : http://127.0.0.1:8000/docs