document.addEventListener('DOMContentLoaded', () => {
    // 1. Theme Toggle
    const themeToggleBtn = document.getElementById('theme-toggle');
    const icon = themeToggleBtn.querySelector('i');
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        icon.classList.remove('fa-moon');
        icon.classList.add('fa-sun');
    }

    themeToggleBtn.addEventListener('click', () => {
        document.body.classList.toggle('light-theme');
        const isLight = document.body.classList.contains('light-theme');
        if (isLight) {
            icon.classList.remove('fa-moon');
            icon.classList.add('fa-sun');
            localStorage.setItem('theme', 'light');
        } else {
            icon.classList.remove('fa-sun');
            icon.classList.add('fa-moon');
            localStorage.setItem('theme', 'dark');
        }
    });

    // 2. Elements & State
    const movieGrid = document.getElementById('movie-grid');
    let movieItems = Array.from(document.querySelectorAll('.movie-grid li'));
    const searchInput = document.getElementById('search-input');
    const decadeFilter = document.getElementById('decade-filter');
    const countryFilter = document.getElementById('country-filter');
    const sortFilter = document.getElementById('sort-filter');
    const favOnlyToggle = document.getElementById('favorites-only');
    const randomBtn = document.getElementById('random-btn');
    const loadMoreBtn = document.getElementById('load-more-btn');
    const loadMoreContainer = document.getElementById('load-more-container');

    let currentLimit = 12;
    let filteredItems = [];

    // Load Favorites from LocalStorage
    let favorites = JSON.parse(localStorage.getItem('my-movies-favorites') || '[]');

    // Initialize items with favorites and skeletons
    movieItems.forEach(item => {
        const imdbId = item.getAttribute('data-imdbid');
        const favBtn = item.querySelector('.favorite-btn');
        if (favorites.includes(imdbId)) {
            favBtn.classList.add('active');
        }

        favBtn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            if (favorites.includes(imdbId)) {
                favorites = favorites.filter(id => id !== imdbId);
                favBtn.classList.remove('active');
            } else {
                favorites.push(imdbId);
                favBtn.classList.add('active');
            }
            localStorage.setItem('my-movies-favorites', JSON.stringify(favorites));
            if (favOnlyToggle.checked) {
                applyFiltersAndPagination();
            }
        });

        // Remove skeleton when loaded
        const img = item.querySelector('.movie-poster');
        if (img) {
            if (img.complete) {
                img.classList.remove('skeleton');
            } else {
                img.addEventListener('load', () => img.classList.remove('skeleton'));
            }
        }
    });

    // 3. Populate Dynamic Filters
    const decades = new Set();
    const countries = new Set();

    movieItems.forEach(item => {
        const year = parseInt(item.getAttribute('data-year'));
        if (!isNaN(year)) {
            decades.add(Math.floor(year / 10) * 10);
        }
        const countryStr = item.getAttribute('data-country');
        if (countryStr) {
            const firstCountry = countryStr.split(',')[0].trim();
            if (firstCountry) countries.add(firstCountry);
        }
    });

    Array.from(decades).sort((a, b) => b - a).forEach(decade => {
        const option = document.createElement('option');
        option.value = decade;
        option.textContent = `${decade}s`;
        decadeFilter.appendChild(option);
    });

    Array.from(countries).sort().forEach(country => {
        const option = document.createElement('option');
        option.value = country;
        option.textContent = country;
        countryFilter.appendChild(option);
    });

    // 4. Sorting, Filtering, Pagination Logic
    function sortItems(items) {
        const sortVal = sortFilter.value;
        if (sortVal === 'default') return items;

        return items.slice().sort((a, b) => {
            if (sortVal === 'title-asc') {
                return a.getAttribute('data-title').localeCompare(b.getAttribute('data-title'));
            } else if (sortVal === 'title-desc') {
                return b.getAttribute('data-title').localeCompare(a.getAttribute('data-title'));
            } else if (sortVal === 'rating-desc') {
                return parseFloat(b.getAttribute('data-rating')) - parseFloat(a.getAttribute('data-rating'));
            } else if (sortVal === 'rating-asc') {
                return parseFloat(a.getAttribute('data-rating')) - parseFloat(b.getAttribute('data-rating'));
            } else if (sortVal === 'year-desc') {
                return parseInt(b.getAttribute('data-year')) - parseInt(a.getAttribute('data-year'));
            } else if (sortVal === 'year-asc') {
                return parseInt(a.getAttribute('data-year')) - parseInt(b.getAttribute('data-year'));
            }
            return 0;
        });
    }

    function applyFiltersAndPagination() {
        const query = searchInput.value.toLowerCase();
        const selectedDecade = decadeFilter.value;
        const selectedCountry = countryFilter.value;
        const showFavs = favOnlyToggle.checked;

        filteredItems = movieItems.filter(item => {
            const title = item.getAttribute('data-title').toLowerCase();
            const year = parseInt(item.getAttribute('data-year')) || 0;
            const decade = Math.floor(year / 10) * 10;
            const firstCountry = (item.getAttribute('data-country') || '').split(',')[0].trim();
            const imdbId = item.getAttribute('data-imdbid') || '';

            const matchesSearch = title.includes(query);
            const matchesDecade = selectedDecade === 'all' || decade.toString() === selectedDecade;
            const matchesCountry = selectedCountry === 'all' || firstCountry === selectedCountry;
            const matchesFav = !showFavs || favorites.includes(imdbId);

            return matchesSearch && matchesDecade && matchesCountry && matchesFav;
        });

        // Sort items
        filteredItems = sortItems(filteredItems);

        // Clear grid and append sorted/filtered items
        movieGrid.innerHTML = '';
        filteredItems.forEach((item, index) => {
            if (index < currentLimit) {
                item.style.display = 'block';
                movieGrid.appendChild(item);
            } else {
                item.style.display = 'none';
                movieGrid.appendChild(item); // Keep them in DOM but hidden
            }
        });

        // Show/Hide Load More
        if (filteredItems.length > currentLimit) {
            loadMoreContainer.style.display = 'block';
        } else {
            loadMoreContainer.style.display = 'none';
        }
    }

    [searchInput, decadeFilter, countryFilter, sortFilter, favOnlyToggle].forEach(el => {
        el.addEventListener((el.tagName === 'INPUT' && el.type === 'text') ? 'input' : 'change', () => {
            currentLimit = 12; // Reset pagination on any filter change
            applyFiltersAndPagination();
        });
    });

    loadMoreBtn.addEventListener('click', () => {
        currentLimit += 12;
        applyFiltersAndPagination();
    });

    // Random Pick
    randomBtn.addEventListener('click', () => {
        if (filteredItems.length === 0) return alert('No movies match your filters!');
        const randomIndex = Math.floor(Math.random() * filteredItems.length);
        const selectedItem = filteredItems[randomIndex];
        selectedItem.querySelector('.movie-poster-link').click(); // Opens Modal
    });

    // Initial load
    applyFiltersAndPagination();

    // 5. Modal Logic
    const modal = document.getElementById('movie-modal');
    const closeBtn = document.getElementById('modal-close');

    // Setup genre filtering logic for tags in modal
    function applyGenreFilter(genreStr) {
        modal.classList.remove('show');
        searchInput.value = genreStr; // Simplest way to filter by genre for now without adding a complex new dropdown logic
        applyFiltersAndPagination();
    }

    movieItems.forEach(item => {
        const link = item.querySelector('.movie-poster-link');
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const imdbId = item.getAttribute('data-imdbid');
            if (imdbId) {
                window.open(`https://www.imdb.com/title/${imdbId}/`, '_blank');
            }
        });
    });

    // 6. Right Side Hover Info Card
    const hoverPanel = document.getElementById('hover-panel');
    const hpBg = document.getElementById('hp-bg');
    const hpTitle = document.getElementById('hp-title');
    const hpYear = document.getElementById('hp-year');
    const hpRating = document.getElementById('hp-rating');
    const hpPlot = document.getElementById('hp-plot');
    const hpDirector = document.getElementById('hp-director');
    const hpActors = document.getElementById('hp-actors');
    const hpGenre = document.getElementById('hp-genre');
    const hpRuntime = document.getElementById('hp-runtime');
    const hpReleased = document.getElementById('hp-released');
    const hpBoxOffice = document.getElementById('hp-boxoffice');
    const hpAwards = document.getElementById('hp-awards');

    const hpOmdbInfo = document.getElementById('hp-omdb-info');
    const hpMediaContainer = document.getElementById('hp-media-container');

    let hoverTimeout = null;
    let currentHoveredMovieId = null;
    const omdbCache = {};

    function fetchOmdbData(imdbId) {
        if (!imdbId) return Promise.resolve(null);
        if (omdbCache[imdbId]) return Promise.resolve(omdbCache[imdbId]);

        return fetch(`https://www.omdbapi.com/?apikey=${OMDB_API_KEY}&i=${imdbId}&plot=short`)
            .then(res => res.json())
            .then(data => {
                if (data.Response === 'True') {
                    omdbCache[imdbId] = data;
                    return data;
                }
                return null;
            })
            .catch(() => null);
    }

    function fetchTrailerData(imdbId) {
        if (!imdbId) return Promise.resolve(null);
        return fetch(`https://api.kinocheck.de/movies?imdb_id=${imdbId}&language=en`)
            .then(res => res.json())
            .then(data => {
                if (data && data.trailer && data.trailer.youtube_video_id) {
                    return data.trailer.youtube_video_id;
                }
                return null;
            })
            .catch(() => null);
    }

    function updateHoverPanel(item, isInstant = false) {
        clearTimeout(hoverTimeout);

        // Set basic info immediately
        const title = item.getAttribute('data-title');
        hpTitle.textContent = title;
        hpYear.textContent = item.getAttribute('data-year');
        hpRating.textContent = item.getAttribute('data-rating');

        const imgEl = item.querySelector('.movie-poster');
        if (imgEl) {
            hpBg.style.backgroundImage = `url('${imgEl.src}')`;
        }

        const imdbId = item.getAttribute('data-imdbid');

        // Prevent reloading the same video if already active
        if (currentHoveredMovieId !== imdbId) {
            currentHoveredMovieId = imdbId;
            // Inject a loading spinner immediately
            hpMediaContainer.innerHTML = `
                <div class="trailer-loader">
                    <div></div><div></div><div></div><div></div>
                </div>
            `;

            fetchTrailerData(imdbId).then(youtubeId => {
                if (youtubeId && currentHoveredMovieId === imdbId) {
                    hpMediaContainer.innerHTML = `<iframe width="100%" height="100%" src="https://www.youtube.com/embed/${youtubeId}?autoplay=1&mute=1&controls=0&modestbranding=1" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>`;
                } else if (currentHoveredMovieId === imdbId) {
                    // Fallback to placeholder or nothing if no trailer
                    const fallbackImg = item.querySelector('.movie-poster');
                    if (fallbackImg) {
                        hpMediaContainer.innerHTML = `<img src="${fallbackImg.src}" alt="${title} Poster" style="width:100%; height:100%; object-fit:contain; filter:brightness(0.8);" />`;
                    } else {
                        hpMediaContainer.innerHTML = `<div style="color:white; display:flex; align-items:center; justify-content:center; width:100%; height:100%;">Trailer Not Available</div>`;
                    }
                }
            });
        }

        // Set loading state for OMDB data
        hpOmdbInfo.classList.add('skeleton-text-container');
        hpPlot.textContent = '';
        hpDirector.textContent = '';
        hpActors.textContent = '';
        hpGenre.textContent = '---';
        hpRuntime.textContent = '---';
        hpReleased.textContent = '';
        hpBoxOffice.textContent = '';
        hpAwards.textContent = '';

        hoverPanel.classList.add('active');

        const executeFetch = () => {
            fetchOmdbData(imdbId).then(data => {
                hpOmdbInfo.classList.remove('skeleton-text-container');
                if (data) {
                    hpPlot.textContent = data.Plot && data.Plot !== 'N/A' ? data.Plot : 'No plot available.';
                    hpDirector.textContent = data.Director && data.Director !== 'N/A' ? data.Director : 'Unknown';
                    hpActors.textContent = data.Actors && data.Actors !== 'N/A' ? data.Actors : 'Unknown';
                    hpGenre.textContent = data.Genre && data.Genre !== 'N/A' ? data.Genre : 'Unknown Genre';
                    hpRuntime.textContent = data.Runtime && data.Runtime !== 'N/A' ? data.Runtime : '---';
                    hpReleased.textContent = data.Released && data.Released !== 'N/A' ? data.Released : 'Unknown';
                    hpBoxOffice.textContent = data.BoxOffice && data.BoxOffice !== 'N/A' ? data.BoxOffice : 'N/A';
                    hpAwards.textContent = data.Awards && data.Awards !== 'N/A' ? data.Awards : 'None';
                } else {
                    hpPlot.textContent = 'Extra details not found.';
                    hpDirector.textContent = '---';
                    hpActors.textContent = '---';
                    hpGenre.textContent = '---';
                    hpRuntime.textContent = '---';
                    hpReleased.textContent = '---';
                    hpBoxOffice.textContent = '---';
                    hpAwards.textContent = '---';
                }
            });
        };

        if (isInstant) {
            executeFetch();
        } else {
            hoverTimeout = setTimeout(executeFetch, 300);
        }
    }

    movieItems.forEach(item => {
        item.addEventListener('mouseenter', () => updateHoverPanel(item));
        // Removed mouseleave to keep panel persistent
    });

    // Default load top-rated movie into panel
    const topRatedMatches = movieItems.filter(item => parseFloat(item.getAttribute('data-rating')) >= 8.5);
    if (topRatedMatches.length > 0) {
        const randomTop = topRatedMatches[Math.floor(Math.random() * topRatedMatches.length)];
        updateHoverPanel(randomTop, true);
    } else if (movieItems.length > 0) {
        updateHoverPanel(movieItems[0], true);
    }
});
