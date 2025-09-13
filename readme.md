# 🌍 GeoSoil — Prédiction du Stock de Carbone Organique (SOC)

Projet de stage : prédiction et cartographie du carbone organique du sol (SOC) dans la région Ferlo–Sine (Sénégal), à partir de profils pédologiques (IRD, AfSP, WoSIS) et d’images Sentinel-2 / Landsat-8, via des modèles de Machine Learning et Deep Learning.  

Déploiement d’une application **Django + PostGIS** dans Docker, avec API REST et cartographie Leaflet.

---

## 🚀 Stack technique

- **PostGIS 16 (extension PostgreSQL 16 + 3.4)**  
- **Django / GeoDjango** avec **Gunicorn**  
- **PyTorch** pour l’entraînement/inférence des MLP  
- **Leaflet** pour la visualisation interactive  
- Conteneurisation via **Docker Compose**  

---

## 🗂️ Arborescence 
- data/ # Données brutes et prétraitées 
- geosoil/ # Code Django (API, modèles, web app)
- notebooks/ # Entraînement / exploration 
- rapport/ # Manuscrit LaTeX et figures
- requirements.txt # Dépendances Python

---

## ⚙️ Services (`docker-compose.yml`)

- **db** : PostGIS 16–3.4  
  - Exposé sur `localhost:15432`  
  - Variables (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`) définies dans `.env` ou dans le `docker-compose.yml`.

- **geosoil** : application Django servie via **Gunicorn**  
  - Exposé sur `localhost:8000`  
  - Dépend de la base PostGIS  
  - Montre les volumes locaux :
    - `./geosoil → /app` (code)  
    - `./data → /data` (données)  
    - `./models → /models` (poids IA)


---

## ▶️ Lancer le projet

### 1. Créer le fichier `.env`
À la racine du projet :

```ini
POSTGRES_DB=geosoil
POSTGRES_USER=magayendiaye
POSTGRES_PASSWORD=DB_PASSWORD
DJANGO_SECRET_KEY=change-me
DJANGO_DEBUG=False
ALLOWED_HOSTS=*
```
### 2. lancer l'application 
``` 
docker compose up -d --build
docker compose exec geosoil python manage.py migrate
docker compose exec geosoil python manage.py createsuperuser
```