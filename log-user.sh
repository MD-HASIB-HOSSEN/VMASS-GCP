#!/bin/sh

DB="/data/vmess_users.db"

sqlite3 "$DB" "CREATE TABLE IF NOT EXISTS connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_ip TEXT UNIQUE,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_blocked BOOLEAN DEFAULT 0
);" 2>/dev/null

if [ -n "$1" ]; then
    sqlite3 "$DB" "INSERT OR REPLACE INTO connections (source_ip, last_seen) VALUES ('$1', CURRENT_TIMESTAMP);" 2>/dev/null
fi