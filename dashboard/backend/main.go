package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

func main() {
	db := openDB()
	defer db.Close()

	mux := http.NewServeMux()

	mux.Handle("GET /api/class", handleClass(db))
	mux.Handle("GET /api/class/matrix", handleClassMatrix(db))
	mux.Handle("GET /api/class/problems", handleClassProblems(db))
	mux.Handle("GET /api/class/persistence", handleClassPersistence(db))
	mux.Handle("GET /api/students", handleStudents(db))
	mux.Handle("GET /api/student/{id}", handleStudent(db))
	mux.Handle("GET /api/practice", handlePractice(db))
	mux.Handle("POST /api/diagnose", handleDiagnose(db))

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	handler := corsMiddleware(mux)
	fmt.Printf("dashboard backend listening on :%s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, handler))
}

func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == http.MethodOptions {
			w.WriteHeader(http.StatusNoContent)
			return
		}
		next.ServeHTTP(w, r)
	})
}
