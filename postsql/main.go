// Command postsql is a fast, read-only, AI-native CLI for PostgreSQL.
package main

import (
	"os"

	"postsql/internal/cli"
)

func main() {
	os.Exit(cli.Execute())
}
