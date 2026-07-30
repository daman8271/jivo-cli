// Command sapb1 is a CLI for the SAP Business One Service Layer: read-only by
// default, with three explicit write commands (draft/post/patch) that preview,
// confirm, and log every write.
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
