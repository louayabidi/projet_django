import re
from difflib import SequenceMatcher
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer, util
import nltk
from django.core.files.storage import default_storage
from django.utils.html import strip_tags
from nltk.util import ngrams
import PyPDF2
import os

nltk.download('punkt')

# Embeddings model (BERT léger)
model = SentenceTransformer('all-MiniLM-L6-v2')

# --- N-grams ---
def get_ngrams(text, n=5):
    tokens = nltk.word_tokenize(text.lower())
    return list(ngrams(tokens, n))

def ngram_similarity(text1, text2, n=5):
    grams1 = set(get_ngrams(text1, n))
    grams2 = set(get_ngrams(text2, n))
    if not grams1 or not grams2:
        return 0.0
    intersection = grams1.intersection(grams2)
    return len(intersection) / (len(grams1) + len(grams2) - len(intersection))  # Jaccard similarity

# --- SequenceMatcher ---
def sequence_similarity(text1, text2):
    return SequenceMatcher(None, text1, text2).ratio()

# --- TF-IDF Cosine Similarity ---
def tfidf_similarity(text1, text2):
    vectorizer = TfidfVectorizer().fit([text1, text2])
    vectors = vectorizer.transform([text1, text2])
    return cosine_similarity(vectors[0], vectors[1])[0][0]

# --- Embeddings Similarity ---
def embedding_similarity(text1, text2):
    emb1 = model.encode(text1, convert_to_tensor=True)
    emb2 = model.encode(text2, convert_to_tensor=True)
    return util.cos_sim(emb1, emb2).item()

# --- Lecture du fichier (TXT ou PDF) ---
def read_book_file(book):
    """Lit le contenu d'un fichier .txt ou .pdf"""
    if book.file:
        file_path = default_storage.path(book.file.name)
        if file_path.endswith('.pdf'):
            try:
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text
                    return text
            except Exception as e:
                raise Exception(f"Erreur lecture PDF : {e}")
        else:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                raise Exception(f"Erreur lecture TXT : {e}")
    return ""

def read_book_content(book):
    """Lit le contenu édité (HTML → texte nettoyé)"""
    if not book.content:
        return ""
    text = strip_tags(book.content)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def read_book_text(book):
    """Lit le contenu nettoyé : fichier .txt OU book.content"""
    # 1. Fichier .txt (priorité)
    if book.file and book.file.name:
        try:
            file_path = default_storage.path(book.file.name)
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return clean_text(f.read())
        except Exception as e:
            print(f"Erreur lecture fichier {book.file.name}: {e}")

    # 2. Fallback : contenu HTML
    return clean_text(book.content)

def clean_text(text):
    """Nettoie le texte : supprime HTML, espaces multiples, ponctuation bruitée"""
    if not text:
        return ""
    text = strip_tags(text)  # Supprime <p>, <b>, etc.
    text = re.sub(r'\s+', ' ', text)  # Espace unique
    text = re.sub(r'[^\w\s.,!?;:\-\'"]', '', text)  # Garde ponctuation utile
    return text.strip().lower()