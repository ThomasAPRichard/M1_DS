from bs4 import BeautifulSoup
import time
import random
import copy

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from fake_useragent import UserAgent
from selenium.webdriver.common.proxy import Proxy, ProxyType

import pandas as pd
import numpy as np


#~~~~~~~~~~~~~~~~~~~~~~~~~~~FONCTION PRINCIPALE~~~~~~~~~~~~~~~~~~~~~~~~~~~#
'''
ANCIENNE VERSION 

def scraping_multi_perfume_info(list_url):
    """
    Scrap les informations de plusieurs parfums depuis une liste d'URLs.
    Retourne un DataFrame avec ces informations.
    """

    all_data = [] 
    ua = UserAgent()

    #✅ Configuration Selenium
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--blink-settings=imagesEnabled=false") # Pas besoin d'images = gain de temps
    options.add_argument("--headless=new")  # Nouvelle version plus rapide du headless
     
    for url in list_url :
        # 2) Création du driver

        options.add_argument(f"user-agent={ua.random}")
        driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options)

        # 3) Récupération du contenu HTML
        driver.get(url)
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        driver.quit()

        # On appelle la fonction qui fait le scraping pour UNE URL
        perfume_info = scrape_perfume_info(soup)
        perfume_info['url'] = url
        # On ajoute le résultat (dict) à la liste all_data
        all_data.append(perfume_info)

    # Convertir la liste de dicts en DataFrame
    all_data_df = pd.DataFrame(all_data)
    return all_data_df
''' 

def scraping_multi_perfume_info(list_url):
    """
    Scrap les informations de plusieurs parfums depuis une liste d'URLs (via Selenium).
    Retourne un DataFrame avec ces informations.
    """

    all_data = []
    ua = UserAgent()

    # Configuration commune de Selenium
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--blink-settings=imagesEnabled=false") # Pas besoin d'images = gain de temps
    options.add_argument("--headless=new") 
    options.add_argument(f"user-agent={ua.random}")
    
    
    # On compte le nombre d'URLs qu'on scrape
    num_url = 0
    for url in list_url:
        num_url += 1
        # Mesurer le temps que ça prend pour scraper les infos de cette url
        url_start_time = time.time()

        # On va réessayer plusieurs fois en cas de 429 Too many requests
        max_retries = 2
        retry_count = 0
        success = False

        while retry_count < max_retries and not success:
            retry_count += 1

            try:
                
                # 1) Création du driver
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()),options=options)
                # 2) Charger la page
                driver.get(url)
                # 3) Parse
                soup = BeautifulSoup(driver.page_source, 'html.parser')

                driver.quit()
                # 4) Détecter si on est sur la page 429
                if is_429_too_many_requests(soup):
                    print(f"\n🚫 429 détecté sur la {num_url}ieme url, tentative {retry_count}/{max_retries}. ")
                    print(f"🚫 pour {url}")
                    temps_attente = max(601, 43**retry_count)  # Attendre 10 minutes ou ~30 Minutes
                    print(f"On attend {temps_attente/60} minutes...\n")
                    time.sleep(temps_attente)  
                else:
                    # 5) Tout va bien, on extrait
                    perfume_info = scrape_perfume_info(soup)
                    perfume_info['url'] = url

                    # On ajoute le résultat (dict) à la liste all_data
                    all_data.append(perfume_info)

                    success = True

            except Exception as e:
                print(f"⚠️ Erreur sur l'URL {url}, tentative {retry_count}: {e}")
                # On peut attendre un peu avant de retenter
                time.sleep(5)
            
        if not success:
            # Au bout de max_retries, on abandonne
            print(f"❌ Echec final pour {url} après {max_retries} essais.")

        # Mesurer le temps de scraping pour cette URL
        url_end_time = time.time()
        url_duration = url_end_time - url_start_time
        print(f"⏱️ Temps de scraping pour {url}: \n temps total ={url_duration:.2f} secondes. \n")


    # Convertir la liste de dicts en DataFrame
    df = pd.DataFrame(all_data)
    return df

#~~~~~~~~~~~~~~~~~~~~~~~~~~~FONCTION SECONDAIRE~~~~~~~~~~~~~~~~~~~~~~~~~~~~~#

def scrape_perfume_info(soup):
    """
    Scrap les infos principales depuis la page Fragrantica d'un parfum.
    Retourne un dictionnaire avec ces informations.
    """
   
    # 2) Extraire les données (nom, marque, etc.)
    votes_dict = extract_all_votes(soup)
    nom, marque = extract_name_and_brand(soup)

    perfume_data = {
        "nom_parfum": nom,
        "marque": marque,
        "nose": extract_nose(soup),
        "launch_year": extract_launch_year(soup),
        "rating_value": extract_rating(soup),
        "rating_count": extract_rating_count(soup),
        "main_accords": extract_main_accords(soup),
        "gender": extract_gender(votes_dict),
        "longevity": extract_longevity(votes_dict),
        "sillage": extract_sillage(votes_dict),
        "price_feeling": extract_price_feeling(votes_dict),    
        "top_notes": extract_pyramid_ingredients(soup, "Top Notes"),
        "middle_notes": extract_pyramid_ingredients(soup, "Middle Notes"),
        "base_notes": extract_pyramid_ingredients(soup, "Base Notes")
    }

    # 3) Retourner le dictionnaire
    return perfume_data


#~~~~~~~~~~~~~~~~~~~~~~~~~~~FONCTIONS INTERMEDIAIRES~~~~~~~~~~~~~~~~~~~~~~~~~~~#
# &) Intermédiare d'intermédiaire
def extract_all_votes(soup):
    """
    Extrait tous les votes de la page sous forme d'un dictionnaire.
    """
    
    votes_dict = {}
    seen_moderate = 0

    # Sélectionner tous les blocs contenant les votes
    vote_rows = soup.select('div.grid-x.grid-margin-x')

    for row in vote_rows:
        category_el = row.select_one('span.vote-button-name')
        votes_el = row.select_one('span.vote-button-legend')

        if category_el and votes_el:
            category = category_el.get_text(strip=True)
            votes = votes_el.get_text(strip=True)

            if category == "moderate":
                    seen_moderate += 1
                    if seen_moderate == 2:
                        category = "average"

            # Vérifier si le vote est bien un nombre    
            if votes.isdigit():
                votes_dict[category] = int(votes)
            

    return votes_dict

# 1-2) Nom du parfum & Marque
def extract_name_and_brand(soup):
    """
    REPARER : On peut aussi extraire le nom et la marque depuis la nom de l'url, ça évite le pb des virgules
    Extrait le nom du parfum et la marque depuis la balise meta 'keywords'.
    """

    canonical_link = soup.find("link", {"rel": "canonical"})
    if canonical_link:
        url = canonical_link.get("href", "")
        # Extraire les parties de l'URL
        parts = url.split("/")
        if len(parts) >= 5:
            brand = parts[4].replace("-", " ").strip()  # La marque est le 5e élément
            name = parts[5].replace("-", " ").strip()  # Le nom est le 6e élément
            return name, brand
    return None, None

#3) Parfumeur
def extract_nose(soup):
    """Extrait le nom du parfumeur"""
    nose_el = soup.select_one('div.cell a[href^="/noses/"]')
    return nose_el.get_text(strip=True) if nose_el else None

#4) Année de sortie
def extract_launch_year(soup):
    """Extrait l'année de sortie du parfum"""
    launch_year = soup.title.text.strip()[-4:] if soup.title else ""
    return launch_year if launch_year.isdigit() else None

#5) Perfume rating
def extract_rating(soup):
    """Extrait la note du parfum"""
    rating_el = soup.select_one('span[itemprop="ratingValue"]')
    return rating_el.get_text(strip=True) if rating_el else None

#6) Nombre de votes
def extract_rating_count(soup):
    """Extrait le nombre de votes"""
    rating_count_el = soup.select_one('span[itemprop="ratingCount"]')
    return rating_count_el.get_text(strip=True) if rating_count_el else None

#7) Accords principaux
def extract_main_accords(soup):
    """Extrait les accords principaux du parfum"""
    main_accords_el = soup.find_all('div', class_='cell accord-box')
    return [element.get_text(strip=True) for element in main_accords_el if element.get_text(strip=True)]

#8) Genre
def extract_gender(votes_dict):
    """Détermine le genre du parfum en fonction des votes extraits."""
    gender_labels = ["female", "more female", "unisex", "more male", "male"]
    gender_votes = [votes_dict.get(label, 0) for label in gender_labels]
    
    if sum(gender_votes) <= 8:
        return None

    female_count = gender_votes[0] + gender_votes[1]
    male_count = gender_votes[3] + gender_votes[4]
    unisex_count = 1.2 * gender_votes[2]

    return max(("female", female_count),("male", male_count),("unisex", unisex_count),key=lambda x: x[1])[0]

#9) Longévité
def extract_longevity(votes_dict):
    """Détermine la longévité dominante en fonction des votes."""
    longevity_labels = ["very weak", "weak", "moderate", "long lasting", "eternal"]
    longevity_votes = [votes_dict.get(label, 0) for label in longevity_labels]
    
    return max(zip(longevity_labels, longevity_votes), key=lambda x: x[1])[0] if sum(longevity_votes) > 8 else None

#10) Sillage
def extract_sillage(votes_dict):
    """Détermine le sillage dominant en fonction des votes."""
    sillage_labels = ["intimate", "average", "strong", "enormous"]
    sillage_votes = [votes_dict.get(label, 0) for label in sillage_labels]

    return max(zip(sillage_labels, sillage_votes), key=lambda x: x[1])[0] if sum(sillage_votes) > 8 else None

#11) Perception du prix
def extract_price_feeling(votes_dict):
    """Détermine la perception du prix en fonction des votes."""
    price_labels = ["way overpriced", "overpriced", "ok", "good value", "great value"]
    price_votes = [votes_dict.get(label, 0) for label in price_labels]

    return max(zip(price_labels, price_votes), key=lambda x: x[1])[0] if sum(price_votes) > 8 else None

#12) Pyramide olfactive
## Par sous partie de la pyramide (notes de tête, de coeur, de fond)
def extract_pyramid_ingredients(soup, pyramid_section):
    """Extrait les ingrédients d'une section de la pyramide olfactive"""
    header = soup.find('h4', string=lambda text: text and pyramid_section in text)
    if not header:
        return []

    # Chercher directement tous les <a> après le header
    div = header.find_next('div')
    return list({a_tag.next_sibling.strip() for a_tag in div.find_all('a') if a_tag.next_sibling}) if div else []


# 13) Too many requests
def is_429_too_many_requests(soup):
    # Vérifie par exemple si <h1><span>429</span> Too Many Requests</h1> existe
    title = soup.find('title')
    if title and 'Too Many' in title.get_text(strip=True):
        return True
    return False