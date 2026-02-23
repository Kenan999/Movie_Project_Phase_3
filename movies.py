"""Command-line interface for managing a movie database using a SQL storage layer."""
import sys
import random
import os
from difflib import get_close_matches

import matplotlib.pyplot as plt
import pycountry
from dotenv import load_dotenv

from movie_storage import movie_storage_sql as storage


NUMBER_GREEN = "\033[38;2;0;255;140m"
SOFT_RED = "\033[38;2;255;99;71m"
RESET = "\033[0m"
SOFT_YELLOW = "\033[38;2;255;204;0m"
SOFT_BLUE = "\033[38;2;100;149;237m"
SOFT_PURPLE = "\033[38;2;186;85;211m"
SOFT_ORANGE = "\033[38;2;255;140;0m"
SOFT_CYAN = "\033[38;2;0;206;209m"
SOFT_PINK = "\033[38;2;255;105;180m"

rare_at = "\033[38;2;0;255;200m"

CONTINUE_MESSAGE = "\nPress Enter to continue..."


def require_logged_user():
    """Prevent guest user from performing actions."""
    active_user_id = storage.get_active_user()
    if active_user_id is None:
        print(f"{SOFT_RED}You must switch user before performing this action.{RESET}")
        input(CONTINUE_MESSAGE)
        return False

    # Check if active user is guest
    users = storage.get_users()
    for user_id, name in users:
        if user_id == active_user_id and name.lower() == "guest":
            print(
                f"{SOFT_RED}Guest user cannot perform this action. Please switch user.{RESET}")
            input(CONTINUE_MESSAGE)
            return False

    return True


def get_valid_rating(prompt):
    """Prompt user until a valid rating between 0 and 10 is entered."""
    while True:
        rating_input = input(prompt).strip()
        try:
            rating = float(rating_input)
            if 0 <= rating <= 10:
                return rating
            print(f"{SOFT_RED}Rating must be between 0 and 10.{RESET}")
        except ValueError:
            print(f"{SOFT_RED}Please enter a valid number between 0 and 10.{RESET}")


def get_valid_title(prompt):
    """Prompt user until a non-empty movie title is entered."""
    while True:
        title = input(prompt).strip()
        if title:
            return title
        print(f"{SOFT_RED}Movie name cannot be empty.{RESET}")


def get_movies_view():
    """Display all stored movies."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    if not movies:
        print("No movies stored yet.")
        input(CONTINUE_MESSAGE)
        return

    print()

    for title in sorted(movies):
        data = movies[title]
        print(f"{title}: {data['rating']} ({data['year']})")

    input(CONTINUE_MESSAGE)


def add_movie_view():
    """Prompt user for a movie title and add it via the storage layer."""
    if not require_logged_user():
        return
    title = input("\nEnter movie name: ").strip()

    if not title:
        print("Title cannot be empty.")
        return

    try:
        result = storage.add_movie(title)
        print(result)
    except ConnectionError as e:
        print(e)

    input(CONTINUE_MESSAGE)


def delete_movie_view():
    """Delete a movie selected by the user."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    while True:
        title = input(
            "\nEnter movie name to delete "
            "(or press Enter to return): "
        ).strip()

        if not title:
            return

        if title in movies:
            storage.delete_movie(title)
            print(f"{NUMBER_GREEN}Movie '{title}' deleted successfully.{RESET}")
            input(CONTINUE_MESSAGE)
            return

        print(
            f"{SOFT_RED}Movie does not exist. "
            f"Enter another name or press Enter to return.{RESET}"
        )


def update_movie_view():
    """Update rating for a selected movie."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    while True:
        title = input(
            "\nEnter movie name to update "
            "(or press Enter to return): "
        ).strip()

        if not title:
            return

        if title in movies:
            break

        print(
            f"{SOFT_RED}Movie does not exist. "
            f"Enter another name or press Enter to return.{RESET}"
        )

    note = input("Enter movie note: ").strip()
    storage.update_movie(title, note)
    print(f"{NUMBER_GREEN}Movie '{title}' successfully updated.{RESET}")
    input(CONTINUE_MESSAGE)


def states_view():
    """Display statistics such as average, median, best and worst movie."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    if not movies:
        print("No movies available.")
        input(CONTINUE_MESSAGE)
        return

    ratings = [m["rating"] for m in movies.values()]
    avg = sum(ratings) / len(ratings)

    sorted_items = sorted(movies.items(), key=lambda x: x[1]["rating"])
    mid = len(sorted_items) // 2

    if len(sorted_items) % 2:
        median = sorted_items[mid][1]["rating"]
    else:
        median = (
            sorted_items[mid - 1][1]["rating"]
            + sorted_items[mid][1]["rating"]
        ) / 2

    best = max(movies.items(), key=lambda x: x[1]["rating"])
    worst = min(movies.items(), key=lambda x: x[1]["rating"])

    print(f"Average rating: {avg:.1f}")
    print(f"Median rating: {median:.1f}")
    print(f"Best movie: {best[0]}, {best[1]['rating']:.1f}")
    print(f"Worst movie: {worst[0]}, {worst[1]['rating']:.1f}")

    input(CONTINUE_MESSAGE)


def random_movie_view():
    """Display a randomly selected movie."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    if not movies:
        print("No movies available.")
        input(CONTINUE_MESSAGE)
        return

    title = random.choice(list(movies.keys()))
    data = movies[title]

    print(f"{NUMBER_GREEN}{title} ({data['rating']}, {data['year']}){RESET}")
    input(CONTINUE_MESSAGE)


def sorted_movies_view():
    """Display movies sorted by rating."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    sorted_items = sorted(movies.items(), key=lambda x: x[1]["rating"])

    for title, data in sorted_items:
        print(f"{title}: {data['rating']} ({data['year']})")

    input(CONTINUE_MESSAGE)


def chronological_movies_view():
    """Display movies sorted by year."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    while True:
        order = input("\nShow latest movies first? (y/n): ").strip().lower()
        if order in ("y", "n"):
            break
        print(f"{SOFT_RED}Please enter 'y' or 'n'.{RESET}")

    reverse = order == "y"

    sorted_items = sorted(
        movies.items(),
        key=lambda x: x[1]["year"],
        reverse=reverse
    )

    for title, data in sorted_items:
        print(f"{title}: {data['year']} ({data['rating']})")

    input(CONTINUE_MESSAGE)


def filter_movies_view():
    """Filter movies by rating and year range."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    min_rating_input = input(
        "Enter minimum rating (leave blank for no minimum rating): "
    ).strip()
    start_year_input = input(
        "Enter start year (leave blank for no start year): "
    ).strip()
    end_year_input = input(
        "Enter end year (leave blank for no end year): "
    ).strip()

    try:
        min_rating = float(min_rating_input) if min_rating_input else None
    except ValueError:
        print(f"{SOFT_RED}Invalid minimum rating.{RESET}")
        input(CONTINUE_MESSAGE)
        return

    try:
        start_year = int(start_year_input) if start_year_input else None
    except ValueError:
        print(f"{SOFT_RED}Invalid start year.{RESET}")
        input(CONTINUE_MESSAGE)
        return

    try:
        end_year = int(end_year_input) if end_year_input else None
    except ValueError:
        print(f"{SOFT_RED}Invalid end year.{RESET}")
        input(CONTINUE_MESSAGE)
        return

    filtered = []

    for title, data in movies.items():
        rating = data["rating"]
        year = data["year"]

        if min_rating is not None and rating < min_rating:
            continue
        if start_year is not None and year < start_year:
            continue
        if end_year is not None and year > end_year:
            continue

        filtered.append((title, year, rating))

    if filtered:
        print("\nFiltered Movies:")
        for title, year, rating in filtered:
            print(f"{title} ({year}): {rating}")
    else:
        print("No movies match the given criteria.")

    input(CONTINUE_MESSAGE)


def search_movie_view():
    """Search movies by title using exact, prefix, and fuzzy matching."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    query = input("\nEnter movie name to search: ").strip().lower()
    if not query:
        return

    titles = list(movies.keys())

    exact = [t for t in titles if t.lower() == query]
    starts = [t for t in titles if t.lower().startswith(query)]
    close = get_close_matches(query, titles, n=5, cutoff=0.4)

    results = list(dict.fromkeys(exact + starts + close))

    if results:
        for title in results:
            data = movies[title]
            print(f"{title}: {data['rating']} ({data['year']})")
    else:
        print("No matching movies found.")

    input(CONTINUE_MESSAGE)


def rating_histogram_view():
    """Generate and save a histogram of movie ratings."""
    if not require_logged_user():
        return
    movies = storage.list_movies()
    ratings = [m["rating"] for m in movies.values()]

    filename = input(
        "\nEnter filename to save histogram (e.g. ratings.png): "
    ).strip() or "ratings.png"

    plt.figure()
    plt.hist(ratings, bins=10, edgecolor="black")
    plt.savefig(filename)
    plt.close()

    print(f"{NUMBER_GREEN}Histogram saved as {filename}{RESET}")
    input(CONTINUE_MESSAGE)


def generate_website_view():
    """Generate static HTML website from template."""
    if not require_logged_user():
        return
    movies = storage.list_movies()

    # Read template
    with open("_static/index_template.html", "r", encoding="utf-8") as file:
        template = file.read()

    # Build movie grid
    movie_grid_parts = []

    if not movies:
        movie_grid_parts.append("""
        <li>
            <div class="movie">
                <div class="movie-title">No movies available</div>
                <div class="movie-year">Please add movies to your database.</div>
            </div>
        </li>
        """)
    else:
        for title, data in movies.items():
            poster = data.get("poster", "")
            year = data["year"]
            rating = data["rating"]
            imdb_id = data.get("imdb_id", "")

            # Extract first country
            country_raw = data.get("country", "")
            first_country = country_raw.split(",")[0].strip()

            # Dynamic ISO lookup using pycountry
            try:
                country_obj = pycountry.countries.search_fuzzy(first_country)[0]
                iso_code = country_obj.alpha_2
            except (LookupError, IndexError):
                iso_code = None

            def iso_to_flag(code):
                if not code:
                    return ""
                return chr(ord(code[0]) + 127397) + chr(ord(code[1]) + 127397)

            flag = iso_to_flag(iso_code)

            # Calculate exact percentage for precision stars
            try:
                numeric_rating = float(rating)
            except ValueError:
                numeric_rating = 0.0

            fill_percentage = min(max(numeric_rating * 10, 0), 100)

            stars_html = f'''
            <div class="stars-outer" title="{rating} / 10">
                <i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i><i class="fa-regular fa-star"></i>
                <div class="stars-inner" style="width: {fill_percentage}%;">
                    <i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i><i class="fa-solid fa-star"></i>
                </div>
            </div>
            '''

            safe_country = country_raw.replace('"', '&quot;')
            safe_title = title.replace('"', '&quot;')

            genre = data.get("genre", "")
            safe_genre = genre.replace('"', '&quot;')
            safe_note = data.get("note", "").replace('"', '&quot;')

            genres = [g.strip() for g in genre.split(",") if g.strip()]
            genre_html = "".join(
                [f'<span class="genre-tag">{g}</span>' for g in genres])

            movie_html = f"""
            <li data-title="{safe_title}" data-rating="{rating}" data-year="{year}" data-country="{safe_country}" data-imdbid="{imdb_id}" data-genre="{safe_genre}" data-note="{safe_note}">
                <div class="movie">
                    <i class="fa-solid fa-heart favorite-btn" title="Toggle Favorite" aria-label="Favorite"></i>
                    <a href="#" class="movie-poster-link">
                        <img class="movie-poster skeleton" src="{poster}" alt="{safe_title}">
                        <div class="movie-hover-overlay">
                            <p class="movie-hover-note">{safe_note or 'Click for more details'}</p>
                        </div>
                    </a>
                    <div class="movie-title">{flag} {title}</div>
                    <div class="movie-year">{year}</div>
                    <div class="movie-rating" title="Rating: {rating}">{stars_html}</div>
                    <div class="movie-genres-container">{genre_html}</div>
                </div>
            </li>
            """
            movie_grid_parts.append(movie_html)

    movie_grid = "\n".join(movie_grid_parts)

    # Replace placeholders
    load_dotenv()
    api_key = os.getenv("API_KEY", "")

    final_html = template.replace(
        "__TEMPLATE_TITLE__", "My Movie Collection"
    ).replace(
        "__TEMPLATE_MOVIE_GRID__", movie_grid
    ).replace(
        "__OMDB_API_KEY__", api_key
    )

    # Write final file
    with open("_static/index.html", "w", encoding="utf-8") as file:
        file.write(final_html)

    print("Website was generated successfully.")
    input(CONTINUE_MESSAGE)


def switch_user_view():
    """Allow user to select or create profile."""
    users = storage.get_users()

    print("\nSelect a user:")
    for idx, (user_id, name) in enumerate(users, start=1):
        print(f"{idx}. {name}")
    print(f"{len(users) + 1}. Create new user")

    choice = input("Enter choice: ").strip()

    if not choice.isdigit():
        return

    choice = int(choice)

    if 1 <= choice <= len(users):
        user_id, name = users[choice - 1]
        storage.set_active_user(user_id)
        print(f"\nWelcome back, {name}! 🎬")
    elif choice == len(users) + 1:
        name = input("Enter new user name: ").strip()
        if not name:
            return

        result = storage.create_user(name)

        # Duplicate username case
        if result == "Username already exists. Try another one.":
            print(f"\n{SOFT_RED}{result}{RESET}")
            input(CONTINUE_MESSAGE)
            return

        # Invalid username case
        if result == "Invalid username.":
            print(f"\n{SOFT_RED}{result}{RESET}")
            input(CONTINUE_MESSAGE)
            return

        # Success case
        normalized = name.strip().capitalize()
        users = storage.get_users()
        for user_id, uname in users:
            if uname == normalized:
                storage.set_active_user(user_id)
                break

        print(f"\n{NUMBER_GREEN}User '{normalized}' created and logged in!{RESET}")

    input(CONTINUE_MESSAGE)


def exit_view():
    """Exit the application."""
    print("Bye!")
    sys.exit()


view = {
    0: {"view_name": "Exit", "body": exit_view},
    1: {"view_name": "ListMovies", "body": get_movies_view},
    2: {"view_name": "AddMovie", "body": add_movie_view},
    3: {"view_name": "DeleteMovie", "body": delete_movie_view},
    4: {"view_name": "UpdateMovie", "body": update_movie_view},
    5: {"view_name": "States", "body": states_view},
    6: {"view_name": "RandomMovie", "body": random_movie_view},
    7: {"view_name": "SearchMovie", "body": search_movie_view},
    8: {"view_name": "MoviesSortedByRating", "body": sorted_movies_view},
    9: {"view_name": "CreateRatingHistogram", "body": rating_histogram_view},
    10: {"view_name": "MoviesChronological", "body": chronological_movies_view},
    11: {"view_name": "FilterMovies", "body": filter_movies_view},
    12: {"view_name": "GenerateWebsite", "body": generate_website_view},
    13: {"view_name": "SwitchUser", "body": switch_user_view},
}


def main():
    """Main menu loop handling user interaction."""
    print("\n******** My Movies Database ********\n")
    for key in sorted(view):
        print(f"{key}. {view[key]['view_name']}")

    empty_attempts = 0
    rotating_colors = [
        SOFT_RED,
        SOFT_YELLOW,
        SOFT_BLUE,
        SOFT_PURPLE,
        SOFT_ORANGE,
        SOFT_CYAN,
        SOFT_PINK,
    ]

    while True:
        # Show active username in prompt
        active_user_id = storage.get_active_user()
        username = "guest"

        if active_user_id is not None:
            users = storage.get_users()
            for user_id, name in users:
                if user_id == active_user_id:
                    username = name
                    break

        # Username color logic
        if username.lower() == "guest":
            user_color = SOFT_RED
        else:
            user_color = NUMBER_GREEN

        prompt = (
            f"{user_color}{username}{RESET}"
            f"{rare_at}@{RESET}"
            f"{SOFT_YELLOW} Enter choice:{RESET} "
        )
        choice = input(prompt).strip()

        if not choice:
            color = rotating_colors[
                empty_attempts % len(rotating_colors)
            ]
            message = "Please enter a menu number."

            if empty_attempts == 0:
                print(f"\n{color}{message}{RESET}", end="", flush=True)
            else:
                print(
                    f"\033[F\r{color}{message}{RESET}",
                    end="",
                    flush=True
                )

            empty_attempts += 1
            continue
        empty_attempts = 0
        print("\033[F\r", end="")

        if choice.isdigit() and int(choice) in view:
            print()
            view[int(choice)]["body"]()

            print("\n******** My Movies Database ********\n")
            for key in sorted(view):
                print(f"{key}. {view[key]['view_name']}")
            continue

        print(f"{SOFT_RED}Invalid choice. Please enter a valid number.{RESET}")


if __name__ == "__main__":
    main()
