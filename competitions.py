# competitions.py
"""
Single source of truth for all FEB competitions scraped by this project.
To add a new competition: append an entry to COMPETITIONS.
"""

COMPETITIONS = {
    "primerafeb": {
        "id":             1,
        "slug":           "primerafeb",
        "label":          "PRIMERAFEB",
        "url_year":       2025,
        "name":           "Primera FEB",
        "playoff_series": [44449],
    },
    "lfendesa": {
        "id":             4,
        "slug":           "lfendesa",
        "label":          "LFENDESA",
        "url_year":       2025,
        "name":           "LF Endesa",
        "playoff_series": [44443],
    },
    "lfchallenge": {
        "id":             67,
        "slug":           "lfchallenge",
        "label":          "LFCHALLENGE",
        "url_year":       2025,
        "name":           "LF Challenge",
        "playoff_series": [],
    },
    "segundafeb": {
        "id":             2,
        "slug":           "segundafeb",
        "label":          "SEGUNDAFEB",
        "url_year":       2025,
        "name":           "Segunda FEB",
        "playoff_series": [],
    },
    "lf2": {
        "id":             9,
        "slug":           "lf2",
        "label":          "LF2",
        "url_year":       2025,
        "name":           "LF-2",
        "playoff_series": [],
    },
    "tercerafeb": {
        "id":             3,
        "slug":           "tercerafeb",
        "label":          "TERCERAFEB",
        "url_year":       2025,
        "name":           "Tercera FEB",
        "playoff_series": [],
    },
    "ligau": {
        "id":             74,
        "slug":           "ligau",
        "label":          "LIGAU",
        "url_year":       2025,
        "name":           "Liga U",
        "playoff_series": [],
    },
}
