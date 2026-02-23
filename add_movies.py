from movie_storage import movie_storage_sql as storage


def main():
    users = storage.get_users()
    test_user_id = None
    for uid, name in users:
        if name == "test_user":
            test_user_id = uid
            break

    if not test_user_id:
        print("User test_user not found, creating...")
        storage.create_user("test_user")
        users = storage.get_users()
        for uid, name in users:
            if name == "test_user":
                test_user_id = uid
                break

    storage.set_active_user(test_user_id)
    print(f"Active user set to {test_user_id}")

    movies = [
        "The Shawshank Redemption", "The Godfather", "The Dark Knight",
        "Pulp Fiction", "Forrest Gump", "The Matrix", "Goodfellas",
        "The Silence of the Lambs", "Se7en", "The Green Mile",
        "Gladiator", "The Prestige", "The Departed", "Whiplash",
        "Fight Club", "Interstellar", "Parasite", "Spirited Away",
        "Back to the Future", "The Lion King", "Jurassic Park",
        "The Terminator", "Terminator 2: Judgment Day", "Alien",
        "Aliens", "Avatar", "Titanic", "The Avengers",
        "Avengers: Endgame", "The Lord of the Rings: The Fellowship of the Ring",
        "The Lord of the Rings: The Two Towers", "The Lord of the Rings: The Return of the King",
        "Star Wars: Episode IV - A New Hope", "Star Wars: Episode V - The Empire Strikes Back",
        "Inception", "Spider-Man: Into the Spider-Verse", "Toy Story",
        "Finding Nemo", "Up", "WALL·E"
    ]

    for m in movies:
        print(f"Adding {m}...")
        res = storage.add_movie(m)
        print(res)


if __name__ == "__main__":
    main()
