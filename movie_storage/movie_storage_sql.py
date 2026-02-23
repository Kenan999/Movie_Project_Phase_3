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

with engine.connect() as init_conn:
    init_conn.execute(text("PRAGMA foreign_keys = ON;"))

    init_conn.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """))

    init_conn.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            year INTEGER NOT NULL,
            rating REAL NOT NULL,
            poster TEXT,
            imdb_id TEXT,
            country TEXT,
            note TEXT DEFAULT '',
            genre TEXT DEFAULT '',
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON DELETE CASCADE,
            UNIQUE(title, user_id)
        )
    """))

    # Add genre column to existing DB if missing
    columns = init_conn.execute(text("PRAGMA table_info(movies)")).fetchall()
    column_names = [col[1] for col in columns]
    if "genre" not in column_names:
        init_conn.execute(
            text("ALTER TABLE movies ADD COLUMN genre TEXT DEFAULT ''"))

    init_conn.commit()

load_dotenv()
API_KEY = os.getenv("API_KEY")
OMDB_URL = "http://www.omdbapi.com/"

_current_user_id = None


# ---------------- USERS ---------------- #

def get_users():
    """Return all users ordered by name."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT id, name FROM users ORDER BY name")
        )
        return result.fetchall()


def create_user(name):
    """Create a new user if it does not already exist."""
    if not name:
        return "Invalid username."

    normalized = name.strip().capitalize()

    with engine.connect() as conn:
        try:
            conn.execute(
                text("INSERT INTO users (name) VALUES (:name)"),
                {"name": normalized}
            )
            conn.commit()
            return "User created successfully."
        except IntegrityError:
            return "Username already exists. Try another one."


def set_active_user(user_id):
    """Set the currently active user ID."""
    global _current_user_id  # pylint: disable=global-statement
    _current_user_id = user_id


def get_active_user():
    """Return the currently active user ID."""
    return _current_user_id


# ---------------- MOVIES ---------------- #

def fetch_movie_from_api(title):
    """Fetch movie metadata from OMDb API."""
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
            "country": data.get("Country", ""),
            "genre": data.get("Genre", "")
        }

    except requests.RequestException as exc:
        raise ConnectionError("OMDb API is not accessible.") from exc


def list_movies():
    """Return all movies belonging to the active user."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT title, year, rating, poster, imdb_id, country, note, genre
                FROM movies
                WHERE user_id = :user_id
            """),
            {"user_id": _current_user_id}
        )
        rows = result.fetchall()

    return {
        row[0]: {
            "year": row[1],
            "rating": row[2],
            "poster": row[3],
            "imdb_id": row[4],
            "country": row[5],
            "note": row[6],
            "genre": row[7] if row[7] is not None else ""
        }
        for row in rows
    }


def add_movie(title, note=""):
    """Add a movie to the active user's collection."""
    if not title or len(title.strip()) < 3:
        return "Movie not found."

    movie = fetch_movie_from_api(title.strip())
    if movie is None:
        return "Movie not found."

    with engine.connect() as conn:
        try:
            conn.execute(
                text("""
                    INSERT INTO movies
                    (title, year, rating, poster, imdb_id, country, note, genre, user_id)
                    VALUES (:title, :year, :rating, :poster, :imdb_id, :country, :note, :genre, :user_id)
                """),
                {
                    "title": movie["title"],
                    "year": movie["year"],
                    "rating": movie["rating"],
                    "poster": movie["poster"],
                    "imdb_id": movie["imdb_id"],
                    "country": movie["country"],
                    "note": note.strip(),
                    "genre": movie.get("genre", ""),
                    "user_id": _current_user_id,
                }
            )
            conn.commit()
            return "Movie added successfully."
        except IntegrityError:
            return "Movie already exists."


def delete_movie(title):
    """Delete a movie from the active user's collection."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                DELETE FROM movies
                WHERE title = :title AND user_id = :user_id
            """),
            {"title": title, "user_id": _current_user_id}
        )
        conn.commit()
        return result.rowcount > 0


def update_movie(title, note):
    """Update the note of a movie for the active user."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                UPDATE movies
                SET note = :note
                WHERE title = :title AND user_id = :user_id
            """),
            {"note": note, "title": title,
             "user_id": _current_user_id}
        )
        conn.commit()
        return result.rowcount > 0
