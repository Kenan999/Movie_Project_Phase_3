"""Utility script to bulk-add predefined movies to a test user."""

from movie_storage import movie_storage_sql as storage


def get_or_create_test_user():
    """Ensure test_user exists and return its user_id."""
    users = storage.get_users()

    for user_id, name in users:
        if name == "Test_user":
            return user_id

    print("User 'test_user' not found. Creating...")
    storage.create_user("test_user")

    users = storage.get_users()
    for user_id, name in users:
        if name == "Test_user":
            return user_id

    return None


def main():
    """Bulk add predefined movies to test_user."""
    user_id = get_or_create_test_user()

    if user_id is None:
        print("Failed to create or retrieve test_user.")
        return

    storage.set_active_user(user_id)
    print(f"Active user set to ID {user_id}")

    movies = [
        "The Shawshank Redemption", "The Godfather", "The Dark Knight",
        "Pulp Fiction", "Forrest Gump", "The Matrix", "Goodfellas",
        "The Silence of the Lambs", "Se7en", "The Green Mile",
        "Gladiator", "The Prestige", "The Departed", "Whiplash",
        "Fight Club", "Interstellar", "Parasite", "Spirited Away",
        "Back to the Future", "The Lion King", "Jurassic Park",
        "The Terminator", "Terminator 2: Judgment Day", "Alien",
        "Aliens", "Avatar", "Titanic", "The Avengers",
        "Avengers: Endgame",
        "The Lord of the Rings: The Fellowship of the Ring",
        "The Lord of the Rings: The Two Towers",
        "The Lord of the Rings: The Return of the King",
        "Star Wars: Episode IV - A New Hope",
        "Star Wars: Episode V - The Empire Strikes Back",
        "Inception", "Spider-Man: Into the Spider-Verse",
        "Toy Story", "Finding Nemo", "Up", "WALL·E",
    ]

    for movie_title in movies:
        print(f"Adding: {movie_title}")
        try:
            result = storage.add_movie(movie_title)
            print(result)
        except ConnectionError as exc:
            print(exc)
            break


if __name__ == "__main__":
    main()
