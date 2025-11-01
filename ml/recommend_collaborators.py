import pandas as pd
from sklearn.preprocessing import MultiLabelBinarizer, MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

# 1️⃣ Charger le dataset
df = pd.read_csv('dataset_users.csv')

# 2️⃣ Préparer les genres
df['genres_authored'] = df['genres_authored'].fillna('')
df['genres_authored'] = df['genres_authored'].apply(lambda x: x.split(',') if x else [])

# 3️⃣ Encoder les genres
mlb = MultiLabelBinarizer()
genres_encoded = mlb.fit_transform(df['genres_authored'])
genres_df = pd.DataFrame(genres_encoded, columns=mlb.classes_, index=df.index)

# 4️⃣ Features numériques
numeric_features = df[['nbr_books_authored', 'nbr_books_collab', 'nbr_collab_accepted', 'nbr_collab_pending', 'nbr_collab_refused']]
scaler = MinMaxScaler()
numeric_scaled = pd.DataFrame(scaler.fit_transform(numeric_features), columns=numeric_features.columns, index=df.index)

# 5️⃣ Combiner toutes les features
features = pd.concat([numeric_scaled, genres_df], axis=1)

# 6️⃣ Calculer la similarité cosine
similarity_matrix = cosine_similarity(features)
similarity_df = pd.DataFrame(similarity_matrix, index=df['user_id'], columns=df['user_id'])

# 7️⃣ Fonction pour obtenir top N recommandations
def get_top_recommendations(user_id, top_n=10):
    scores = similarity_df.loc[user_id].drop(user_id)
    top_users = scores.sort_values(ascending=False).head(top_n)
    return top_users

# 8️⃣ Afficher recommandations
print("===== Top 10 collaborateurs recommandés =====\n")
for user_id, username in zip(df['user_id'], df['username']):
    top_users = get_top_recommendations(user_id)
    print(f"Utilisateur {username} (id={user_id}):")
    for uid, score in top_users.items():
        print(f"   - id={uid} | score={score:.3f}")
    print("\n----------------------------------------\n")

# 9️⃣ Exporter le dataset ML final
df.to_csv('dataset_users_ml.csv', index=False)
