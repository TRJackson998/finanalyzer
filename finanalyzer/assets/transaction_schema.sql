DROP TABLE IF EXISTS transaction;
CREATE TABLE transaction (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    description TEXT,
    original_description TEXT,
    category TEXT,
    original_category TEXT,
    amount REAL NOT NULL,
    status TEXT,
);