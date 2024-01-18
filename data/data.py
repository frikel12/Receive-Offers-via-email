import MySQLdb.cursors
import MySQLdb
from sentence_transformers import SentenceTransformer, util
import numpy as np


db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'db': 'webscraping',
}


def connect_to_database():
    return MySQLdb.connect(**db_config)


def close_database_connection(connection, cursor):
    cursor.close()
    connection.close()


def get_keywords():
    connection = connect_to_database()
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"SELECT k.name, k.user_id FROM keywords k, users u WHERE u.id=k.user_id AND u.receive_email=1")
    keywords = cursor.fetchall()
    keywords = list(keywords)

    user_keywords = {}

    for keyword in keywords:
        user_id = keyword['user_id']
        if user_id in user_keywords:
            user_keywords[user_id].append(keyword['name'])
        else:
            user_keywords[user_id] = [keyword['name']]

    result = {user_id: ' '.join(keywords) for user_id, keywords in user_keywords.items()}

    return result


def get_data():
    connection = connect_to_database()
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"SELECT * FROM post_list")
    data = cursor.fetchall()
    data = list(data)

    return data


def get_description_liste(data):
    posts = []
    for x in data:
        posts.append(x['post_description'])
    return posts


# similarity using a huggin face model for sentence similarity
def calculate_top_similarities_indices(keywords, posts, model_name, top_k=10):
    model = SentenceTransformer(model_name)

    phrase_embedding = model.encode(keywords, convert_to_tensor=True)
    sentence_embeddings = model.encode(posts, convert_to_tensor=True)

    cosine_similarities = util.pytorch_cos_sim(phrase_embedding, sentence_embeddings)
    cosine_similarities = cosine_similarities.cpu().numpy()

    top_indices = (-cosine_similarities[0]).argsort()[:top_k]

    return top_indices


# similarity using simple search
def calculate_top_similarities_indices_search(keywords, posts, top_k=10):
    keyword_tokens = set(keywords.lower().split())
    post_tokens_list = [set(post.lower().split()) for post in posts]

    similarities = [len(keyword_tokens.intersection(post_tokens)) / len(keyword_tokens.union(post_tokens)) for post_tokens in post_tokens_list]

    top_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)[:top_k]

    return top_indices


def get_top10(posts, keywords):
    posts = np.array(posts)
    posts_description = get_description_liste(posts)
    similarity = {}
    for k, v in keywords.items():
        indices = calculate_top_similarities_indices_search(v, posts_description)
        similar_posts = posts[indices]
        for post in similar_posts:
            post.pop('post_description')
        similarity[k] = similar_posts

    return similarity


def get_email_by_id(id):
    connection = connect_to_database()
    cursor = connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(f"SELECT * FROM users WHERE id={id}")

    data = cursor.fetchone()
    return data['email']




