"""SQL storage layer for the Movies project using OMDb API and SQLite."""

import os

import requests
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError

# Define the database URL
DB_URL = "sqlite:///data/movies.db"

# Create the engine; log statements only if the database doesn't exist yet
db_exists = os.path.exists("data/movies.db")
engine = create_engine(DB_URL, echo=not db_exists)

# Create the movies table if it does not exist
with engine.connect() as connection:
    connection.execute(text("""
        CREATE TABLE IF NOT EXISTS movies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT UNIQUE NOT NULL,
            year INTEGER NOT NULL,
            rating REAL NOT NULL,
            poster TEXT
        )
    """))
    connection.commit()

load_dotenv()

API_KEY = os.getenv("API_KEY")
OMDB_URL = "http://www.omdbapi.com/"

def fetch_movie_from_api(title):
    """Fetch movie data from OMDb API."""
    params = {
        "apikey": API_KEY,
        "t": title,
        "r": "json"
    }

    try:
        response = requests.get(OMDB_URL, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if data.get("Response") == "False":
            return None

        return {
            "title": data["Title"],
            "year": int(data["Year"]),
            "rating": float(data["imdbRating"]) if data["imdbRating"] != "N/A" else 0.0,
            "poster": data["Poster"]
        }

    except requests.RequestException as exc:
        raise ConnectionError("OMDb API is not accessible.") from exc


def list_movies():
    """Retrieve all movies from the database."""
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT title, year, rating, poster FROM movies")
        )
        movies = result.fetchall()

    return {
        row[0]: {
            "year": row[1],
            "rating": row[2],
            "poster": row[3]
        }
        for row in movies
    }


def add_movie(title):
    """Add movie from OMDb API into database with strict validation."""

    # Reject empty or very short titles
    if not title or len(title.strip()) < 3:
        return "Movie not found."

    movie = fetch_movie_from_api(title.strip())

    # If API returned nothing
    if movie is None:
        return "Movie not found."

    # Enforce exact title match (case-insensitive)
    if movie["title"].strip().lower() != title.strip().lower():
        return "Movie not found."

    with engine.connect() as connection:
        try:
            connection.execute(
                text("""
                    INSERT INTO movies (title, year, rating, poster)
                    VALUES (:title, :year, :rating, :poster)
                """),
                movie
            )
            connection.commit()
            return "Movie added successfully."
        except IntegrityError:
            return "Movie already exists."


def delete_movie(title):
    """Delete a movie by title from the database."""
    with engine.connect() as connection:
        result = connection.execute(
            text("DELETE FROM movies WHERE title = :title"),
            {"title": title}
        )
        connection.commit()
        return result.rowcount > 0


def update_movie(title, rating):
    """Update a movie's rating in the database."""
    with engine.connect() as connection:
        result = connection.execute(
            text("UPDATE movies SET rating = :rating WHERE title = :title"),
            {"rating": rating, "title": title}
        )
        connection.commit()
        return result.rowcount > 0
