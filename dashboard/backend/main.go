package main

import (
	"bufio"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
)

func loadEnv(candidates []string) {
	for _, path := range candidates {
		f, err := os.Open(path)
		if err != nil {
			continue
		}
		scanner := bufio.NewScanner(f)
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if line == "" || strings.HasPrefix(line, "#") {
				continue
			}
			parts := strings.SplitN(line, "=", 2)
			if len(parts) != 2 {
				continue
			}
			key := strings.TrimSpace(parts[0])
			val := strings.Trim(strings.TrimSpace(parts[1]), `'"`)
			if os.Getenv(key) == "" {
				os.Setenv(key, val)
			}
		}
		f.Close()
		break
	}
}

func main() {
	loadEnv([]string{"../../.env", ".env"})
	db := openDB()
	defer db.Close()

	mux := http.NewServeMux()

	mux.Handle("GET /api/class", handleClass(db))
	mux.Handle("GET /api/class/matrix", handleClassMatrix(db))
	mux.Handle("GET /api/class/problems", handleClassProblems(db))
	mux.Handle("GET /api/class/persistence", handleClassPersistence(db))
	mux.Handle("GET /api/students", handleStudents(db))
	mux.Handle("GET /api/student/{id}", handleStudent(db))
	mux.Handle("GET /api/problems", handleProblems(db))
	mux.Handle("GET /api/practice", handlePractice(db))
	mux.Handle("POST /api/diagnose", handleDiagnose(db))
	mux.Handle("POST /api/reteach", handleReteach(db))

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
