from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from difflib import SequenceMatcher
from sentence_transformers import SentenceTransformer, util
import nltk

from django.core.files.storage import default_storage
from nltk.util import ngrams
import pdfplumber 
import PyPDF2 


nltk.download('punkt')

# Modèle pour embeddings (BERT léger, gratuit)
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
    try:
        if not book.file:
            return book.synopsis or ""  # Fallback to synopsis if no file
        file_path = default_storage.path(book.file.name)
        if file_path.endswith('.pdf'):
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() or ""
                return text
        else:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
    except Exception as e:
        raise Exception(f"Erreur lors de la lecture du fichier : {str(e)}")