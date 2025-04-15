CONFIG = {
    "window": {
        "title": "Star Wars Unlimited - Card Viewer",
        "width_ratio": 0.6,
        "height_ratio": 0.6,
        "font": {
            "family": "Arial",
            "size": 10
        }
    },
    "data": {
        "image_folder": "images",
        "cards_file": "cards.json",
        "collection_file": "collection.json",
        "deck_folder": "decks"
    },
    "api": {
        "base_url": "https://api.swu-db.com",
        "headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        },
        "timeout": 30,
        "retry_attempts": 3
    },
    "default_sets": ['sor', 'shd', 'twi', 'jtl'],
    "search": {
        "fuzzy_threshold": 80
    }
}