package main

import (
	"fmt"
	"sort"

	"github.com/spf13/cobra"
)

// newEndpointsCmd prints the read allowlist this binary was generated from, so a
// user can see exactly what is reachable without reading the vault.
func newEndpointsCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "endpoints",
		Short: "List every endpoint this CLI is allowed to read",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			hosts := make([]string, 0, len(allowedReads))
			for h := range allowedReads {
				hosts = append(hosts, h)
			}
			sort.Strings(hosts)
			for _, h := range hosts {
				paths := make([]string, 0, len(allowedReads[h]))
				for p := range allowedReads[h] {
					paths = append(paths, p)
				}
				sort.Strings(paths)
				fmt.Printf("\n%s  (%d reads)\n", h, len(paths))
				for _, p := range paths {
					fmt.Printf("  %s\n", p)
				}
			}
			fmt.Printf("\ntotal: %d read endpoints. Writes, exports and unproven (UNKNOWN)\n", allowlistSize())
			fmt.Println("endpoints are absent by construction — see vault/Swiggy-Instamart-Endpoints.md.")
			return nil
		},
	}
}
