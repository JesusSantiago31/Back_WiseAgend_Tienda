Despliegue en Render - Instrucciones rápidas

1) Agrega el repo a Render y crea un nuevo "Web Service".
2) Build command: (vacío) - Render detectará Python.
3) Start command: `gunicorn app:app`
4) En "Environment" → "Secrets/Environment Variables" añade:
   - `SERVICE_ACCOUNT_JSON`: pega aquí el JSON completo del service account (como un string JSON).
   - `API_TOKEN` (opcional): si quieres sobreescribir el token.
5) Opcional: si prefieres, en vez de pasar el JSON completo, configura integración de GCP si Render lo soporta para usar ADC.

Notas:
- No subas `serviceAccountKey.json` al repositorio. Si estuvo expuesto, revoca la clave en GCP y crea una nueva.
- Locamente puedes exportar: `export SERVICE_ACCOUNT_JSON="$(cat serviceAccountKey.json | jq -c .)"` (Unix) o en Windows usar una forma equivalente.
