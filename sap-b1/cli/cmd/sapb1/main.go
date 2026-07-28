// Command sapb1 is a read-only CLI for the SAP Business One Service Layer.
package main

import (
	"context"
	"fmt"
	"os"

	"sapb1/internal/cli"
)

func main() {
	root := cli.NewRootCmd()

	err := root.ExecuteContext(context.Background())
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(cli.ExitCodeFor(err))
	}
}
