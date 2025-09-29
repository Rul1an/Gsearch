# Gsearch
**Webcrawler voor WBSO** - Google Search Scraper

Een eenvoudige Google search scraper gebouwd in Python om zoekresultaten te verzamelen voor WBSO-gerelateerd onderzoek.

## Functies

- **Eenvoudige Google zoekopdrachten**: Verzamel zoekresultaten voor elke query
- **Aanpasbare resultaten**: Stel het aantal gewenste resultaten in
- **Rate limiting**: Ingebouwde vertraging tussen requests om respectvol te scrapen
- **Gestructureerde output**: Krijg titel, link en snippet voor elk resultaat
- **Foutafhandeling**: Robuuste error handling voor netwerk- en parsing-problemen

## Installatie

1. Clone deze repository:
```bash
git clone https://github.com/Rul1an/Gsearch.git
cd Gsearch
```

2. Installeer de vereiste dependencies:
```bash
pip install -r requirements.txt
```

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
python3 test_gsearch.py
```

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
- `lxml` - XML/HTML parser backend

## Licentie

Dit project is ontwikkeld voor WBSO webcrawling doeleinden.
