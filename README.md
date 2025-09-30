# Gsearch
**Webcrawler voor WBSO** - Google Search Scraper

Een eenvoudige Google search scraper gebouwd in Python om zoekresultaten te verzamelen voor WBSO-gerelateerd onderzoek.

## Functies

- **Eenvoudige Google zoekopdrachten**: Verzamel zoekresultaten voor elke query
- **Aanpasbare resultaten**: Stel het aantal gewenste resultaten in
- **Rate limiting**: Ingebouwde vertraging tussen requests om respectvol te scrapen
- **Exponentiële backoff**: Automatische vertraging bij CAPTCHA- en netwerkfouten
- **Gestructureerde output**: Krijg titel, link en snippet voor elk resultaat
- **Foutafhandeling**: Robuuste error handling voor netwerk- en parsing-problemen

## Installatie

1. Clone deze repository:
```bash
git clone https://github.com/Rul1an/Gsearch.git
cd Gsearch
```

2. Installeer de vereiste dependencies (alleen pure-Python pakketten, dus geen native build stap nodig):
```bash
pip install -r requirements.txt
```

3. Start de API lokaal met Uvicorn:
```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

De interactieve documentatie is beschikbaar op `http://localhost:8000/docs`.

## Gebruik

### Basis gebruik

```python
from gsearch import GoogleScraper

# Initialiseer de scraper
scraper = GoogleScraper(delay=1.0)

# Voer een zoekopdracht uit
results = scraper.search("WBSO subsidie Nederland", num_results=10)

# Print de resultaten
for result in results:
    print(f"Titel: {result['title']}")
    print(f"Link: {result['link']}")
    print(f"Snippet: {result['snippet']}")
    print("-" * 40)
```

### Geformatteerde output

```python
scraper = GoogleScraper()
scraper.search_and_print("WBSO voorwaarden", num_results=5)
```

### Voorbeeld script uitvoeren

```bash
python3 example.py
```

### HTTP API gebruiken

Vraag resultaten op via de FastAPI-endpoints. Bijvoorbeeld:

```bash
curl "http://localhost:8000/search?query=WBSO%20subsidie&num_results=5"
```

Dit retourneert een JSON-payload met dezelfde structuur als de Python-interface.

Een eenvoudige healthcheck is beschikbaar via:

```bash
curl http://localhost:8000/health
```

### Configuratie via omgevingsvariabelen

De FastAPI-service kan worden geconfigureerd zonder codewijzigingen:

- `GSEARCH_DELAY`: basisvertraging (in seconden) tussen requests en als startpunt voor backoff. Standaard `1.0`.
- `GSEARCH_PROXIES`: kommagescheiden lijst met proxy-URL's (bijv. `http://p1:8080,http://p2:8080`).
- `GSEARCH_USER_AGENTS`: kommagescheiden lijst met user-agent strings die afwisselend worden gebruikt.

Voorbeeld bij gebruik van Render of Docker:

```bash
export GSEARCH_DELAY=2.5
export GSEARCH_PROXIES="http://proxy1:8080,http://proxy2:8080"
export GSEARCH_USER_AGENTS="agent1,agent2,agent3"
uvicorn app:app --reload
```

## API Referentie

### GoogleScraper Class

#### `__init__(delay: float = 1.0)`
Initialiseer de Google scraper.

**Parameters:**
- `delay`: Vertraging tussen requests in seconden (standaard: 1.0)

#### `search(query: str, num_results: int = 10) -> List[Dict[str, str]]`
Voer een Google zoekopdracht uit.

**Parameters:**
- `query`: De zoekterm
- `num_results`: Aantal gewenste resultaten (standaard: 10)

**Returns:**
- Lijst van dictionaries met keys: 'title', 'link', 'snippet'

#### `search_and_print(query: str, num_results: int = 10) -> None`
Voer een zoekopdracht uit en print geformatteerde resultaten.

## Voorbeelden voor WBSO

```python
# WBSO-specifieke zoekopdrachten
scraper = GoogleScraper()

# Zoek naar WBSO subsidie informatie
wbso_results = scraper.search("WBSO subsidie aanvragen RVO", 5)

# Zoek naar WBSO voorwaarden
voorwaarden = scraper.search("WBSO voorwaarden 2024", 3)

# Zoek naar WBSO rapportage
rapportage = scraper.search("WBSO rapportage verplichtingen", 3)
```

## Belangrijke opmerkingen

- **Respectvol scrapen**: De scraper heeft een ingebouwde vertraging tussen requests
- **User-Agent**: Gebruikt een browser user-agent om detectie te vermijden
- **Rate limiting**: Pas de delay aan op basis van je gebruik
- **Robots.txt**: Respecteer altijd de robots.txt van websites
- **Legaal gebruik**: Gebruik alleen voor legale doeleinden en onderzoek

## Tests uitvoeren

```bash
pytest -q
```

## Deployen op Render.com

Maak een nieuwe **Web Service** aan en gebruik de volgende commando's:

- **Build Command**

  ```bash
  pip install -r requirements.txt
  ```

- **Start Command**

  ```bash
  gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:${PORT}
  ```

Render injecteert automatisch de `PORT`-omgeving variabele. Zorg ervoor dat je service als runtime "Python 3" gebruikt.

## Structuur

```
Gsearch/
├── README.md           # Deze documentatie
├── requirements.txt    # Python dependencies
├── gsearch.py         # Hoofd scraper module
├── example.py         # Voorbeelden van gebruik
└── test_gsearch.py    # Unit tests
```

## Dependencies

- `requests` - Voor HTTP requests
- `beautifulsoup4` - Voor HTML parsing

## Licentie

Dit project is ontwikkeld voor WBSO webcrawling doeleinden.
