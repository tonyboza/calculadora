import requests
from bs4 import BeautifulSoup
import json
import time
import random
from urllib.parse import urljoin
import os

BASE_URL = "https://www.carfolio.com"
DELAY = 5  # Segundos entre requests
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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
            time.sleep(DELAY + random.uniform(0, 2))  # Delay aleatorio
            response = self.session.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Error al obtener {url}: {str(e)}")
            return None

    def extract_brands(self):
        """Extrae todas las marcas disponibles"""
        print("Extrayendo lista de marcas...")
        soup = self.get_soup(f"{BASE_URL}/car-specifications")
        if not soup:
            return []
            
        brands = []
        brand_container = soup.find('div', {'class': 'manufacturers'})
        if brand_container:
            for link in brand_container.find_all('a'):
                brand = {
                    'name': link.text.strip(),
                    'url': urljoin(BASE_URL, link['href']),
                    'models': []
                }
                brands.append(brand)
        
        print(f"Encontradas {len(brands)} marcas")
        return brands

    def extract_models(self, brand_url):
        """Extrae modelos para una marca específica"""
        soup = self.get_soup(brand_url)
        if not soup:
            return []
            
        models = []
        model_table = soup.find('table', {'class': 'carlist'})
        if model_table:
            for row in model_table.find_all('tr')[1:]:  # Saltar encabezado
                cols = row.find_all('td')
                if len(cols) >= 2:
                    model_link = cols[0].find('a')
                    if model_link:
                        model = {
                            'name': model_link.text.strip(),
                            'url': urljoin(BASE_URL, model_link['href']),
                            'years': cols[1].text.strip(),
                            'specs': {}
                        }
                        models.append(model)
        return models

    def extract_specs(self, model_url):
        """Extrae especificaciones técnicas detalladas"""
        if model_url in self.visited_urls:
            return None
        self.visited_urls.add(model_url)
        
        soup = self.get_soup(model_url)
        if not soup:
            return None
            
        specs = {}
        
        # Extraer datos principales
        title = soup.find('h1', {'class': 'title'})
        if title:
            specs['model'] = title.text.strip()
        
        # Extraer tabla de especificaciones
        spec_tables = soup.find_all('table', {'class': 'specs'})
        for table in spec_tables:
            for row in table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) == 2:
                    key = cols[0].text.strip().lower().replace(' ', '_')
                    value = cols[1].text.strip()
                    specs[key] = value
        
        # Extraer dimensiones específicas
        dimensions = {}
        dim_section = soup.find('h3', text='Dimensions')
        if dim_section:
            dim_table = dim_section.find_next('table')
            if dim_table:
                for row in dim_table.find_all('tr'):
                    cols = row.find_all('td')
                    if len(cols) == 2:
                        key = cols[0].text.strip().lower().replace(' ', '_')
                        value = cols[1].text.strip()
                        dimensions[key] = value
        specs['dimensions'] = dimensions
        
        return specs

    def save_data(self, filename='carfolio_data.json'):
        """Guarda los datos en un archivo JSON"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"Datos guardados en {filename}")

    def run(self, max_brands=None, max_models_per_brand=None):
        """Ejecuta el proceso completo de scraping"""
        brands = self.extract_brands()
        
        if max_brands:
            brands = brands[:max_brands]
        
        for brand in brands:
            print(f"\nProcesando marca: {brand['name']}")
            models = self.extract_models(brand['url'])
            
            if max_models_per_brand:
                models = models[:max_models_per_brand]
            
            for model in models:
                print(f"  Modelo: {model['name']} ({model['years']})")
                specs = self.extract_specs(model['url'])
                if specs:
                    model['specs'] = specs
                    print(f"    Especificaciones obtenidas")
                else:
                    print("    No se pudieron obtener especificaciones")
                
                # Guardar progreso periódicamente
                if len(models) > 5 and models.index(model) % 5 == 0:
                    self.save_data()
            
            brand['models'] = models
            self.data[brand['name']] = brand
            self.save_data()
        
        print("\nScraping completado")

if __name__ == "__main__":
    scraper = CarfolioScraper()
    
    # Ejemplo: Extraer solo 2 marcas y 3 modelos por marca (para prueba)
    scraper.run(max_brands=2, max_models_per_brand=3)