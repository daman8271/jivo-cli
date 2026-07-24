package main

import (
	"fmt"
	"net/url"

	"github.com/spf13/cobra"
)

// Shared leaf-command builders. Every cmd_<section>.go assembles its command
// group from these so the whole CLI is uniform and read-only by construction —
// each builder only ever calls app.get / app.post (GET or POST-to-read).

// simpleGet: a plain authenticated GET of a fixed path.
func simpleGet(app *App, group, use, short, host, path string) *cobra.Command {
	return &cobra.Command{
		Use:   use,
		Short: short,
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return app.get(group+" "+use, host, path)
		},
	}
}

// queryGet: a GET whose path takes an optional raw --query string
// ("k=v&k2=v2"), for list/grid endpoints whose exact filter params are not yet
// verified. --query is appended verbatim.
func queryGet(app *App, group, use, short, host, path string) *cobra.Command {
	var q string
	c := &cobra.Command{
		Use:   use,
		Short: short,
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			p := path
			if q != "" {
				sep := "?"
				if containsRune(p, '?') {
					sep = "&"
				}
				p += sep + q
			}
			return app.get(group+" "+use, host, p)
		},
	}
	c.Flags().StringVar(&q, "query", "", "raw query string appended to the path (e.g. \"page=1&size=50\")")
	return c
}

// getByID: a GET of a path template with a single {id} segment (pathFmt uses %s).
func getByID(app *App, group, use, short, host, pathFmt, argName string) *cobra.Command {
	return &cobra.Command{
		Use:   use + " <" + argName + ">",
		Short: short,
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			p := fmt.Sprintf(pathFmt, url.PathEscape(args[0]))
			return app.get(group+" "+use, host, p)
		},
	}
}

// postRead: a POST-to-read (list/search) taking an optional --body JSON.
func postRead(app *App, group, use, short, host, path, defaultBody string) *cobra.Command {
	var body string
	c := &cobra.Command{
		Use:   use,
		Short: short,
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			b := defaultBody
			if body != "" {
				b = body
			}
			var bb []byte
			if b != "" {
				bb = []byte(b)
			}
			return app.post(group+" "+use, host, path, bb)
		},
	}
	c.Flags().StringVar(&body, "body", "", "raw JSON request body (POST-to-read)")
	return c
}

func containsRune(s string, r rune) bool {
	for _, c := range s {
		if c == r {
			return true
		}
	}
	return false
}
