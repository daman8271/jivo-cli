package main

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"
	"strings"

	"github.com/spf13/cobra"
)

// flipkart-portal — READ-ONLY exploration CLI over JIVO's Flipkart Seller Hub +
// Vendor Hub. Generated from the vault READ allowlist (captures/wired-reads.tsv).
// Three-layer read-only guarantee: (1) GET-only transport, (2) READ allowlist,
// (3) go test. It consumes an existing session cookie jar (env) and never logs in.

func main() {
	root := &cobra.Command{
		Use:   "flipkart-portal",
		Short: "Read-only explorer for JIVO's Flipkart Seller Hub + Vendor Hub",
		Long: "flipkart-portal — READ-ONLY. Every command is a GET against a READ-classified\n" +
			"endpoint. It reads the session cookie jar from the environment\n" +
			"(FLIPKART_SELLER_COOKIE / FLIPKART_VENDOR_COOKIE [+ _CSRF]) and never mints a\n" +
			"session. Writes are impossible: the transport refuses any non-GET verb.",
	}
	root.AddCommand(doctorCmd(), whoamiCmd(), listCmd())
	for _, g := range groupCommands() {
		root.AddCommand(g)
	}
	if err := root.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, "error:", err)
		os.Exit(1)
	}
}

// groupCommands builds one cobra group per section, each with a subcommand per
// wired READ endpoint.
func groupCommands() []*cobra.Command {
	byGroup := map[string][]Endpoint{}
	for _, e := range registry {
		byGroup[e.Group] = append(byGroup[e.Group], e)
	}
	names := make([]string, 0, len(byGroup))
	for g := range byGroup {
		names = append(names, g)
	}
	sort.Strings(names)
	var cmds []*cobra.Command
	for _, g := range names {
		eps := byGroup[g]
		grp := &cobra.Command{Use: g, Short: fmt.Sprintf("%d read endpoints", len(eps))}
		for _, ep := range eps {
			ep := ep
			var asJSON bool
			var params []string
			var id string
			sc := &cobra.Command{
				Use:   ep.Name,
				Short: fmt.Sprintf("GET %s%s  [%s]", ep.Host, ep.Path, ep.Class),
				RunE: func(cmd *cobra.Command, args []string) error {
					return runEndpoint(ep, id, params, asJSON)
				},
			}
			sc.Flags().BoolVar(&asJSON, "json", false, "pretty-print JSON response")
			sc.Flags().StringArrayVar(&params, "param", nil, "query param k=v (repeatable)")
			sc.Flags().StringVar(&id, "id", "", "value to substitute for a {id} path param")
			grp.AddCommand(sc)
		}
		cmds = append(cmds, grp)
	}
	return cmds
}

func runEndpoint(ep Endpoint, id string, params []string, asJSON bool) error {
	path := ep.Path
	if strings.Contains(path, "{id}") {
		if id == "" {
			return fmt.Errorf("endpoint needs a path id: pass --id <value> (path is %s)", ep.Path)
		}
		path = strings.ReplaceAll(path, "{id}", id)
	}
	pm := map[string]string{}
	for _, p := range params {
		kv := strings.SplitN(p, "=", 2)
		if len(kv) == 2 {
			pm[kv[0]] = kv[1]
		}
	}
	body, code, err := newClient().GET(ep.Host, path, pm)
	if err != nil {
		fmt.Fprintf(os.Stderr, "HTTP %d: %v\n", code, err)
	}
	if asJSON {
		var v interface{}
		if json.Unmarshal(body, &v) == nil {
			b, _ := json.MarshalIndent(v, "", "  ")
			fmt.Printf("HTTP %d\n%s\n", code, b)
			return nil
		}
	}
	fmt.Printf("HTTP %d  (%d bytes)\n%s\n", code, len(body), string(body))
	return nil
}

func doctorCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "doctor",
		Short: "Report configuration + reachability (read-only)",
		RunE: func(cmd *cobra.Command, args []string) error {
			sc, _ := cookieForHost("seller.flipkart.com")
			vc, _ := cookieForHost("vendorhub.flipkart.com")
			fmt.Println("flipkart-portal doctor — READ-ONLY")
			fmt.Printf("  wired READ endpoints : %d across %d groups\n", len(registry), countGroups())
			fmt.Printf("  FLIPKART_SELLER_COOKIE: %s\n", present(sc))
			fmt.Printf("  FLIPKART_VENDOR_COOKIE: %s\n", present(vc))
			fmt.Println("  transport            : GET-only (writes refused before socket open)")
			// health probe: a harmless GET that needs no auth to prove reachability
			_, code, _ := newClient().GET("seller.flipkart.com", "/napi/printing/certificate", nil)
			fmt.Printf("  seller reachability  : GET /napi/printing/certificate -> HTTP %d\n", code)
			return nil
		},
	}
}

func whoamiCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "auth",
		Short: "Session identity (non-secret facts only)",
		RunE: func(cmd *cobra.Command, args []string) error {
			fmt.Println("Seller Hub  : ecom8@jivo.in  sellerId e56b4e65e27e4162  (JIVOMART)")
			fmt.Println("Vendor Hub  : gurvinder@jivo.in (6 vendors) / infinite@jivo.in (3 vendors)")
			fmt.Println("This CLI consumes an existing session jar from env; it never logs in (G9).")
			return nil
		},
	}
}

func listCmd() *cobra.Command {
	var group string
	c := &cobra.Command{
		Use:   "list",
		Short: "List all wired READ endpoints (optionally --group X)",
		RunE: func(cmd *cobra.Command, args []string) error {
			for _, e := range registry {
				if group != "" && e.Group != group {
					continue
				}
				fmt.Printf("%-24s %-40s %s %s%s\n", e.Group, e.Name, e.Method, e.Host, e.Path)
			}
			return nil
		},
	}
	c.Flags().StringVar(&group, "group", "", "filter by group")
	return c
}

func present(s string) string {
	if strings.TrimSpace(s) == "" {
		return "NOT SET (reads will 401 until you export the jar)"
	}
	return "set"
}

func countGroups() int {
	m := map[string]bool{}
	for _, e := range registry {
		m[e.Group] = true
	}
	return len(m)
}
