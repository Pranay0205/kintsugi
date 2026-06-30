package main

import (
	"database/sql"
	"log"
	"os"

	_ "modernc.org/sqlite"
)

func openDB() *sql.DB {
	path := os.Getenv("DB_PATH")
	if path == "" {
		path = "../kintsugi.db"
	}
	db, err := sql.Open("sqlite", path+"?_journal=WAL&_timeout=5000")
	if err != nil {
		log.Fatalf("open db: %v", err)
	}
	db.SetMaxOpenConns(10)
	db.SetMaxIdleConns(5)
	return db
}
