import re
import requests
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize
import nltk
from difflib import SequenceMatcher
from django.utils.html import strip_tags
import urllib.parse
import random
import time
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os

# === CONFIG ===
nltk.download('punkt', quiet=True)
logger = logging.getLogger(__name__)


GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', 'AIzaSyCB1GhGwX0hQ8cTgsha6T4okv9fHgF6mSA')
GOOGLE_CSE_ID = os.getenv('GOOGLE_CSE_ID', '240cfc3a93eda4cd3')

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36',
]

# --- Utility Functions ---
def sequence_similarity(text1, text2):
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

def clean_text(text):
    if not text:
        return ""
    text = strip_tags(text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s.,!?;:\-\'"]', '', text)
    return text.strip().lower()

def extract_key_sentences(text, num_sentences=3):
    """Extract most meaningful sentences for plagiarism checking"""
    sentences = sent_tokenize(text)
    # Filter sentences: must be 30+ chars and contain meaningful words
    scored = []
    for s in sentences:
        if len(s) > 30 and len(s) < 200:  # Not too short, not too long
            words = s.lower().split()
            # Score by unique words and length
            unique_words = len(set(words))
            if unique_words > 5:  # Must have at least 5 unique words
                scored.append((s, unique_words))
    
    scored.sort(key=lambda x: x[1], reverse=True)
    return [s[0] for s in scored[:num_sentences]]

def tfidf_similarity(text1, text2):
    vectorizer = TfidfVectorizer()
    try:
        vectors = vectorizer.fit_transform([text1, text2])
        return cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
    except:
        return 0.0

def ngram_similarity(text1, text2, n=5):
    text1 = clean_text(text1)
    text2 = clean_text(text2)
    
    if len(text1) < n or len(text2) < n:
        return 0.0
    
    ngrams1 = set(text1[i:i+n] for i in range(len(text1) - n + 1))
    ngrams2 = set(text2[i:i+n] for i in range(len(text2) - n + 1))
    
    intersection = ngrams1 & ngrams2
    union = ngrams1 | ngrams2
    
    return len(intersection) / len(union) if union else 0.0

# For embedding_similarity
try:
    from sentence_transformers import SentenceTransformer
    embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
except ImportError:
    embedding_model = None
    print("[WARNING] sentence-transformers not installed.")

def embedding_similarity(text1, text2):
    if embedding_model is None:
        return 0.0
    
    text1 = clean_text(text1)
    text2 = clean_text(text2)
    
    if not text1 or not text2:
        return 0.0
    
    emb1 = embedding_model.encode([text1])
    emb2 = embedding_model.encode([text2])
    
    return cosine_similarity(emb1, emb2)[0][0]

# === IMPROVED WEB PLAGIARISM WITH GOOGLE API ===
def check_web_plagiarism_google_api(text, threshold=0.75):
    """
    Use Google Custom Search API for better results.
    Get your API key from: https://console.developers.google.com/
    Get your CSE ID from: https://programmablesearchengine.google.com/
    """
    print(f"🎯 [PLAGIAT-GOOGLE-API] Début analyse")
    
    if not GOOGLE_API_KEY or GOOGLE_API_KEY == 'YOUR_API_KEY':
        print("❌ [PLAGIAT-GOOGLE-API] API key manquante!")
        return []
    
    clean_text_content = clean_text(text)
    sentences = extract_key_sentences(clean_text_content, 3)
    
    web_matches = []
    session = requests.Session()
    
    for i, sentence in enumerate(sentences):
        clean_sentence = clean_text(sentence)
        if len(clean_sentence) < 30:
            continue

        print(f"🔎 [PLAGIAT-GOOGLE-API] Recherche {i+1}/3: '{clean_sentence[:60]}...'")
        
        # Use Google Custom Search API
        api_url = "https://www.googleapis.com/customsearch/v1"
        params = {
            'key': GOOGLE_API_KEY,
            'cx': GOOGLE_CSE_ID,
            'q': f'"{clean_sentence}"',  # Exact match
            'num': 5  # Get top 5 results
        }
        
        try:
            time.sleep(1)  # Rate limiting
            response = session.get(api_url, params=params, timeout=10)
            
            if response.status_code != 200:
                print(f"❌ [PLAGIAT-GOOGLE-API] Erreur API: {response.status_code}")
                continue
            
            data = response.json()
            items = data.get('items', [])
            print(f"📈 [PLAGIAT-GOOGLE-API] Résultats trouvés: {len(items)}")
            
            for item in items:
                url_page = item.get('link')
                title = item.get('title', 'Sans titre')
                snippet = item.get('snippet', '')
                
                if not url_page:
                    continue
                
                print(f"🔗 [PLAGIAT-GOOGLE-API] Test: {title[:50]}...")
                
                # Check snippet first for quick match
                snippet_sim = sequence_similarity(clean_sentence, clean_text(snippet))
                
                if snippet_sim >= threshold:
                    print(f"🚨 [PLAGIAT-GOOGLE-API] MATCH dans snippet! {snippet_sim*100:.1f}%")
                    web_matches.append({
                        'sentence': clean_sentence[:200],
                        'similarity': round(snippet_sim * 100, 2),
                        'url': url_page,
                        'title': title,
                        'snippet': snippet[:300]
                    })
                    continue
                
                # Fetch full page for deeper analysis
                try:
                    time.sleep(random.uniform(1, 2))
                    headers = {'User-Agent': random.choice(USER_AGENTS)}
                    page_resp = session.get(url_page, headers=headers, timeout=15)
                    
                    if page_resp.status_code != 200:
                        continue
                    
                    page_text = clean_text(page_resp.text)
                    page_sentences = sent_tokenize(page_text)
                    
                    max_sim = 0
                    best_snippet = ""
                    
                    for page_sent in page_sentences[:200]:  # Check first 200 sentences
                        if len(page_sent) < 20:
                            continue
                        
                        clean_page_sent = clean_text(page_sent)
                        
                        # Calculate multiple similarity scores
                        scores = [
                            sequence_similarity(clean_sentence, clean_page_sent),
                            tfidf_similarity(clean_sentence, clean_page_sent),
                            ngram_similarity(clean_sentence, clean_page_sent, n=5)
                        ]
                        
                        if embedding_model:
                            scores.append(embedding_similarity(clean_sentence, clean_page_sent))
                        
                        avg_sim = sum(scores) / len(scores)
                        
                        if avg_sim > max_sim:
                            max_sim = avg_sim
                            best_snippet = page_sent[:300]
                    
                    print(f"📊 [PLAGIAT-GOOGLE-API] Similarité max: {max_sim*100:.1f}%")
                    
                    if max_sim >= threshold:
                        print(f"🚨 [PLAGIAT-GOOGLE-API] MATCH! {max_sim*100:.1f}%")
                        web_matches.append({
                            'sentence': clean_sentence[:200],
                            'similarity': round(max_sim * 100, 2),
                            'url': url_page,
                            'title': title,
                            'snippet': best_snippet
                        })
                
                except Exception as e:
                    print(f"❌ [PLAGIAT-GOOGLE-API] Erreur page: {e}")
                    continue
        
        except Exception as e:
            print(f"❌ [PLAGIAT-GOOGLE-API] Erreur recherche: {e}")
            continue
    
    print(f"🏁 [PLAGIAT-GOOGLE-API] Fin: {len(web_matches)} match(s)")
    return web_matches


# === FALLBACK: IMPROVED BING SCRAPING ===
def check_web_plagiarism_bing(text, threshold=0.75):
    """
    Improved Bing scraping with better filtering and error handling
    """
    print(f"🎯 [PLAGIAT-BING] Début analyse")
    
    clean_text_content = clean_text(text)
    sentences = extract_key_sentences(clean_text_content, 3)
    
    web_matches = []
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504, 429])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    
    for i, sentence in enumerate(sentences):
        clean_sentence = clean_text(sentence)
        if len(clean_sentence) < 30:
            continue

        print(f"🔎 [PLAGIAT-BING] Recherche {i+1}/3: '{clean_sentence[:60]}...'")
        
        # Search with exact phrase
        query = urllib.parse.quote(f'"{clean_sentence}"')
        url = f"https://www.bing.com/search?q={query}&setlang=en"
        
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.bing.com/'
        }

        try:
            time.sleep(random.uniform(2, 4))
            response = session.get(url, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"❌ [PLAGIAT-BING] Erreur: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')
            results = soup.find_all('li', class_='b_algo')
            
            # Filter out irrelevant results (Google, Wikipedia about search engines, etc.)
            filtered_results = []
            blacklist = ['google.com', 'wikipedia.org/wiki/Google', 'bing.com', 'yahoo.com']
            
            for result in results[:10]:
                link_tag = result.find('h2').find('a') if result.find('h2') else None
                if not link_tag:
                    continue
                
                url_page = link_tag.get('href', '')
                if any(blocked in url_page.lower() for blocked in blacklist):
                    continue
                
                filtered_results.append(result)
            
            print(f"📈 [PLAGIAT-BING] Résultats valides: {len(filtered_results)}")
            
            if len(filtered_results) == 0:
                print(f"⚠️ [PLAGIAT-BING] Aucun résultat pertinent pour cette phrase")
                continue
            
            for result in filtered_results[:5]:
                link_tag = result.find('h2').find('a')
                url_page = link_tag.get('href')
                title = link_tag.get_text().strip()
                
                print(f"🔗 [PLAGIAT-BING] Test: {title[:60]}...")

                try:
                    time.sleep(random.uniform(1, 2))
                    page_resp = session.get(url_page, headers=headers, timeout=20)
                    
                    if page_resp.status_code != 200:
                        continue

                    page_text = clean_text(page_resp.text)
                    page_sentences = sent_tokenize(page_text)
                    
                    max_sim = 0
                    best_snippet = ""
                    
                    for page_sent in page_sentences[:200]:
                        if len(page_sent) < 20:
                            continue
                        
                        clean_page_sent = clean_text(page_sent)
                        
                        scores = [
                            sequence_similarity(clean_sentence, clean_page_sent),
                            tfidf_similarity(clean_sentence, clean_page_sent),
                            ngram_similarity(clean_sentence, clean_page_sent, n=5)
                        ]
                        
                        if embedding_model:
                            scores.append(embedding_similarity(clean_sentence, clean_page_sent))
                        
                        avg_sim = sum(scores) / len(scores)
                        
                        if avg_sim > max_sim:
                            max_sim = avg_sim
                            best_snippet = page_sent[:300]

                    print(f"📊 [PLAGIAT-BING] Similarité max: {max_sim*100:.1f}%")
                    
                    if max_sim >= threshold:
                        print(f"🚨 [PLAGIAT-BING] MATCH! {max_sim*100:.1f}%")
                        web_matches.append({
                            'sentence': clean_sentence[:200],
                            'similarity': round(max_sim * 100, 2),
                            'url': url_page,
                            'title': title,
                            'snippet': best_snippet
                        })
                    
                except Exception as e:
                    print(f"❌ [PLAGIAT-BING] Erreur page: {e}")
                    continue
                    
        except Exception as e:
            print(f"❌ [PLAGIAT-BING] Erreur recherche: {e}")
            continue

    print(f"🏁 [PLAGIAT-BING] Fin: {len(web_matches)} match(s)")
    return web_matches


# === MAIN FUNCTION ===
def check_web_plagiarism(text, threshold=0.75, use_google_api=True):
    """
    Main plagiarism checker - tries Google API first, falls back to Bing scraping
    """
    if use_google_api and GOOGLE_API_KEY and GOOGLE_API_KEY != 'YOUR_API_KEY':
        return check_web_plagiarism_google_api(text, threshold)
    else:
        print("⚠️ Google API non configurée, utilisation de Bing scraping...")
        return check_web_plagiarism_bing(text, threshold)