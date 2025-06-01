import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin

BASE_URL = "https://www.carfolio.com"
MAKES_URL = f"{BASE_URL}/car-specifications"  # URL correcta para listado de marcas
DELAY = 3  # segundos entre requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
}

class CarfolioScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.data = {}
        self.visited_urls = set()

    def get_soup(self, url):
        """Obtiene el contenido HTML con manejo de errores"""
        try:
            if url in self.visited_urls:
                return None
                
            time.sleep(DELAY + random.uniform(0, 1))
            print(f"Accediendo a: {url}")
            res = self.session.get(url)
            res.raise_for_status()
            self.visited_urls.add(url)
            return BeautifulSoup(res.text, 'html.parser')
        except Exception as e:
            print(f"Error al acceder a {url}: {str(e)}")
            return None

    def extract_brands(self):
        """Extrae todas las marcas disponibles desde la página correcta"""
        print("Extrayendo lista de marcas...")
        soup = self.get_soup(MAKES_URL)
        if not soup:
            return []

        brands = []
        manufacturer_div = soup.find('div', {'class': 'manufacturers'})
        if manufacturer_div:
            for a in manufacturer_div.find_all('a', href=True):
                brand_name = a.text.strip()
                if brand_name and not brand_name.startswith('http'):
                    brands.append({
                        "name": brand_name,
                        "url": urljoin(BASE_URL, a['href']),
                        "models": []
                    })
        print(f"Encontradas {len(brands)} marcas")
        return brands

    def extract_models(self, brand):
        """Extrae modelos para una marca específica"""
        print(f"Extrayendo modelos para {brand['name']}...")
        soup = self.get_soup(brand['url'])
        if not soup:
            return []

        models = []
        model_table = soup.find('table', {'class': 'carlist'})
        if model_table:
            for row in model_table.find_all('tr')[1:]:  # Saltar encabezado
                cols = row.find_all('td')
                if len(cols) >= 2:
                    model_link = cols[0].find('a', href=True)
                    if model_link:
                        model_name = model_link.text.strip()
                        model_url = urljoin(BASE_URL, model_link['href'])
                        
                        # Algunos modelos tienen años en el nombre, los separamos
                        years = cols[1].text.strip() if len(cols) > 1 else ''
                        
                        models.append({
                            "name": model_name,
                            "url": model_url,
                            "years": years,
                            "specs": {}
                        })
        return models

    def extract_specs(self, model):
        """Extrae especificaciones técnicas detalladas"""
        soup = self.get_soup(model['url'])
        if not soup:
            return None

        specs = {
            "dimensions": {},
            "technical": {}
        }

        # Extraer nombre completo del modelo
        title = soup.find('h1', {'class': 'title'})
        if title:
            specs['full_name'] = title.text.strip()

        # Extraer todas las tablas de especificaciones
        for table in soup.find_all('table', {'class': 'specs'}):
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 2:
                    key = cols[0].text.strip().lower().replace(' ', '_')
                    value = cols[1].text.strip()
                    specs['technical'][key] = value

        # Extraer dimensiones específicas
        dimensions_header = soup.find('h3', string=lambda t: 'Dimensions' in str(t))
        if dimensions_header:
            dim_table = dimensions_header.find_next('table')
            if dim_table:
                for row in dim_table.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) == 2:
                        key = cols[0].text.strip().lower().replace(' ', '_')
                        value = cols[1].text.strip()
                        specs['dimensions'][key] = value

        return specs

    def run(self, max_brands=None, max_models_per_brand=None):
        """Ejecuta el proceso completo de scraping"""
        brands = self.extract_brands()
        
        if not brands:
            print("No se encontraron marcas. Verifica la URL o la estructura de la página.")
            return

        if max_brands:
            brands = brands[:max_brands]

        for brand in brands:
            print(f"\nProcesando marca: {brand['name']}")
            models = self.extract_models(brand)
            
            if max_models_per_brand:
                models = models[:max_models_per_brand]

            for model in models:
                print(f"  Procesando modelo: {model['name']}")
                model['specs'] = self.extract_specs(model)
                if model['specs']:
                    print("    ✓ Especificaciones obtenidas")
                else:
                    print("    ✗ No se pudieron obtener especificaciones")

            brand['models'] = models
            self.data[brand['name']] = brand
            self.save_data()  # Guardar progreso después de cada marca

        print("\n✅ Scraping completado con éxito")

    def save_data(self, filename="carfolio_data.json"):
        """Guarda los datos en un archivo JSON"""
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"💾 Datos guardados en {filename}")

if __name__ == "__main__":
    scraper = CarfolioScraper()
    
    # Para prueba: extraer 2 marcas y 2 modelos por marca
    scraper.run(max_brands=2, max_models_per_brand=2)