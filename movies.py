"""Command-line interface for managing a movie database using a SQL storage layer."""
import sys
import random
from difflib import get_close_matches
import matplotlib.pyplot as plt
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

CONTINUE_MESSAGE = "\nPress Enter to continue..."




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

    rating = get_valid_rating("Enter new rating (0–10): ")
    storage.update_movie(title, rating)

    print(f"{NUMBER_GREEN}Movie '{title}' updated successfully.{RESET}")
    input(CONTINUE_MESSAGE)


def states_view():
    """Display statistics such as average, median, best and worst movie."""
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
    movies = storage.list_movies()

    sorted_items = sorted(movies.items(), key=lambda x: x[1]["rating"])

    for title, data in sorted_items:
        print(f"{title}: {data['rating']} ({data['year']})")

    input(CONTINUE_MESSAGE)


def chronological_movies_view():
    """Display movies sorted by year."""
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

            movie_html = f"""
            <li>
                <div class="movie">
                    <img class="movie-poster" src="{poster}" alt="{title}">
                    <div class="movie-title">{title}</div>
                    <div class="movie-year">{year}</div>
                </div>
            </li>
            """
            movie_grid_parts.append(movie_html)

    movie_grid = "\n".join(movie_grid_parts)

    # Replace placeholders
    final_html = template.replace(
        "__TEMPLATE_TITLE__", "My Movie Collection"
    ).replace(
        "__TEMPLATE_MOVIE_GRID__", movie_grid
    )

    # Write final file
    with open("_static/index.html", "w", encoding="utf-8") as file:
        file.write(final_html)

    print("Website was generated successfully.")
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
        choice = input("Enter choice: ").strip()

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
