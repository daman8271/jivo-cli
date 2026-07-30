package main

import (
	"fmt"
	"net/url"
	"strings"

	"github.com/spf13/cobra"
)

// Shared leaf builders. Every generated command is assembled from these, so the
// whole CLI is read-only by construction: they can only ever call app.get or
// app.postRead, both of which route through the transport guardrail.

// readGet: an allowlisted GET. --query appends a raw query string; --id fills a
// single path placeholder if the endpoint has one.
func readGet(app *App, group, use, short, host, path string) *cobra.Command {
	var q, id string
	c := &cobra.Command{
		Use:   use,
		Short: short,
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			p, err := fillPath(path, id)
			if err != nil {
				return err
			}
			if q != "" {
				sep := "?"
				if strings.Contains(p, "?") {
					sep = "&"
				}
				p += sep + q
			}
			return app.get(group+" "+use, host, p)
		},
	}
	c.Flags().StringVar(&q, "query", "", `raw query string, e.g. "page=1&size=50"`)
	if hasPlaceholder(path) {
		c.Flags().StringVar(&id, "id", "", "id to substitute into the path (required)")
	}
	return c
}

// readPost: an allowlisted POST-to-read. Swiggy serves most reads this way, so
// --body carries the query. The default body is "{}" which is enough for the
// simple list endpoints; the richer ones want a real query object and the section
// note documents its shape.
func readPost(app *App, group, use, short, host, path string) *cobra.Command {
	var body, id string
	c := &cobra.Command{
		Use:   use,
		Short: short,
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			p, err := fillPath(path, id)
			if err != nil {
				return err
			}
			var b []byte
			if body != "" {
				b = []byte(body)
			}
			return app.postRead(group+" "+use, host, p, b)
		},
	}
	c.Flags().StringVar(&body, "body", "", "raw JSON request body (this is a POST-to-read)")
	if hasPlaceholder(path) {
		c.Flags().StringVar(&id, "id", "", "id to substitute into the path (required)")
	}
	return c
}

func hasPlaceholder(path string) bool {
	return strings.ContainsAny(path, "{$")
}

// fillPath substitutes a caller-supplied id into a templated path. The id is
// path-escaped so it cannot inject extra segments and slip past the allowlist.
func fillPath(path, id string) (string, error) {
	if !hasPlaceholder(path) {
		return path, nil
	}
	if id == "" {
		return "", fmt.Errorf("this endpoint is templated (%s) — pass --id", path)
	}
	esc := url.PathEscape(id)
	out := path
	for _, tok := range placeholders(path) {
		out = strings.Replace(out, tok, esc, 1)
	}
	return out, nil
}

// placeholders returns the {name} / ${name} tokens in a path, in order.
func placeholders(path string) []string {
	var out []string
	for i := 0; i < len(path); i++ {
		if path[i] == '{' || (path[i] == '$' && i+1 < len(path) && path[i+1] == '{') {
			j := strings.IndexByte(path[i:], '}')
			if j < 0 {
				break
			}
			out = append(out, path[i:i+j+1])
			i += j
		}
	}
	return out
}
