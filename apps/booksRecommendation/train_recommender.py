import pandas as pd
from implicit.als import AlternatingLeastSquares
from scipy.sparse import coo_matrix
from apps.book.models import Book, User

def train_als_model():
    user_book_data = []
    for user in User.objects.all():
        for book in user.favorite_books.all():
            user_book_data.append((user.id, book.id, 1))  # interaction = 1 si favori

    df = pd.DataFrame(user_book_data, columns=["user_id", "book_id", "interaction"])

    # Sparse matrix items × users
    sparse_matrix = coo_matrix(
        (df['interaction'], (df['book_id'], df['user_id']))
    )

    model = AlternatingLeastSquares(factors=20, regularization=0.1, iterations=20)
    model.fit(sparse_matrix)

    return model, sparse_matrix
