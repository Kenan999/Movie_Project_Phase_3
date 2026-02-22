"""SQL storage layer for the Movies project using OMDb API and SQLite."""

import os
import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

# Database
DB_URL = "sqlite:///data/movies.db"
os.makedirs("data", exist_ok=True)
engine = create_engine(DB_URL, echo=False)

with engine.connect() as connection:
    connection.execute(text("PRAGMA foreign_keys = ON;"))

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """))

    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year INTEGER NOT NULL,
            rating REAL NOT NULL,
            poster TEXT,
            imdb_id TEXT,
            country TEXT,
            note TEXT DEFAULT '',
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE,
            UNIQUE(title, user_id)
        )
    """))

    connection.commit()

load_dotenv()
API_KEY = os.getenv("API_KEY")
OMDB_URL = "http://www.omdbapi.com/"

current_user_id = None


# ---------------- USERS ---------------- #

def get_users():
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT id, name FROM users ORDER BY name")
        )
        return result.fetchall()


def create_user(name):
    if not name:
        return "Invalid username."

    normalized = name.strip().capitalize()

    with engine.connect() as connection:
        try:
            connection.execute(
                text("INSERT INTO users (name) VALUES (:name)"),
                {"name": normalized}
            )
            connection.commit()
            return "User created successfully."
        except IntegrityError:
            return "Username already exists. Try another one."


def set_active_user(user_id):
    global current_user_id
    current_user_id = user_id


def get_active_user():
    return current_user_id


# ---------------- MOVIES ---------------- #

def fetch_movie_from_api(title):
    params = {"apikey": API_KEY, "t": title, "r": "json"}

    try:
        response = requests.get(OMDB_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("Response") == "False":
            return None

        return {
            "title": data["Title"],
            "year": int(data["Year"]),
            "rating": float(data["imdbRating"])
            if data["imdbRating"] != "N/A" else 0.0,
            "poster": data["Poster"],
            "imdb_id": data.get("imdbID", ""),
            "country": data.get("Country", "")
        }

    except requests.RequestException as exc:
        raise ConnectionError("OMDb API is not accessible.") from exc


def list_movies():
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                SELECT title, year, rating, poster, imdb_id, country, note
                FROM movies
                WHERE user_id = :user_id
            """),
            {"user_id": current_user_id}
        )
        rows = result.fetchall()

    return {
        row[0]: {
            "year": row[1],
            "rating": row[2],
            "poster": row[3],
            "imdb_id": row[4],
            "country": row[5],
            "note": row[6]
        }
        for row in rows
    }


def add_movie(title, note=""):
    if not title or len(title.strip()) < 3:
        return "Movie not found."

    movie = fetch_movie_from_api(title.strip())
    if movie is None:
        return "Movie not found."

    with engine.connect() as connection:
        try:
            connection.execute(
                text("""
                    INSERT INTO movies
                    (title, year, rating, poster, imdb_id, country, note, user_id)
                    VALUES (:title, :year, :rating, :poster, :imdb_id, :country, :note, :user_id)
                """),
                {
                    "title": movie["title"],
                    "year": movie["year"],
                    "rating": movie["rating"],
                    "poster": movie["poster"],
                    "imdb_id": movie["imdb_id"],
                    "country": movie["country"],
                    "note": note.strip(),
                    "user_id": current_user_id,
                }
            )
            connection.commit()
            return "Movie added successfully."
        except IntegrityError:
            return "Movie already exists."


def delete_movie(title):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                DELETE FROM movies
                WHERE title = :title AND user_id = :user_id
            """),
            {"title": title, "user_id": current_user_id}
        )
        connection.commit()
        return result.rowcount > 0


def update_movie(title, note):
    with engine.connect() as connection:
        result = connection.execute(
            text("""
                UPDATE movies
                SET note = :note
                WHERE title = :title AND user_id = :user_id
            """),
            {"note": note, "title": title,
             "user_id": current_user_id}
        )
        connection.commit()
        return result.rowcount > 0