# train_recommender.py
import pandas as pd
from surprise import Dataset, Reader, KNNBasic
from surprise.model_selection import train_test_split
import pickle

# ⚠️ Assure-toi que dataset_users_enriched.csv existe et a les colonnes correctes
df = pd.read_csv('dataset_users_enriched.csv')

# --- Fonction pour calculer la similarité de genres ---
def genre_similarity(genres1, genres2):
    if not isinstance(genres1, str):
        genres1 = ""
    if not isinstance(genres2, str):
        genres2 = ""
    set1 = set(genres1.split(',')) if genres1 else set()
    set2 = set(genres2.split(',')) if genres2 else set()
    if not set1 or not set2:
        return 0.0
    return len(set1 & set2) / len(set1 | set2)

# --- Création d'une matrice "user_id x user_id" avec un score combiné ---
users = df['user_id'].tolist()
rows = []
for idx, row in df.iterrows():
    for idx2, row2 in df.iterrows():
        if row['user_id'] != row2['user_id']:
            score = row2['nbr_collab_accepted'] + genre_similarity(row['genres_authored'], row2['genres_authored'])
            rows.append([row['user_id'], row2['user_id'], score])

ratings_df = pd.DataFrame(rows, columns=['user_id', 'collaborator_id', 'score'])

# --- Préparer pour Surprise ---
reader = Reader(rating_scale=(0, ratings_df['score'].max()))
data = Dataset.load_from_df(ratings_df[['user_id', 'collaborator_id', 'score']], reader)

# Split train/test
trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

# --- Algorithme de recommandation (KNN basé sur les utilisateurs) ---
sim_options = {'name': 'cosine', 'user_based': True}
algo = KNNBasic(sim_options=sim_options)
algo.fit(trainset)

# --- Évaluer sur le testset ---
predictions = algo.test(testset)

# Optionnel : afficher quelques prédictions
print("Exemple de prédictions :")
for pred in predictions[:10]:
    print(f"user {pred.uid} -> collaborator {pred.iid} | score prédit {pred.est:.3f}")

# --- Sauvegarder le modèle pour utilisation future ---
with open('recommender_model.pkl', 'wb') as f:
    pickle.dump(algo, f)

print("✅ Modèle de recommandation entraîné et sauvegardé dans recommender_model.pkl")
