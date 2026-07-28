package cli

import (
	"errors"
	"fmt"
	"io"
	"sort"
	"strings"
	"text/tabwriter"

	"github.com/spf13/cobra"

	"sapb1/internal/catalog"
	"sapb1/internal/client"
	"sapb1/internal/errs"
)

// maxSuggestions caps how many "did you mean?" names we print on a miss.
const maxSuggestions = 5

// newEntitiesCmd lists every service/entity in the embedded catalog. Fully
// offline — it never touches the network.
func newEntitiesCmd() *cobra.Command {
	var search string
	var readOnly bool

	cmd := &cobra.Command{
		Use:   "entities",
		Short: "List all Service Layer services/entities from the embedded catalog (offline)",
		Long: `entities lists every service/entity in the embedded Service Layer catalog
— all 498 of them — with its operation count, the HTTP methods it exposes, and
whether it is readable (has a GET). This works with zero network access: it
reads only the catalog compiled into the binary.

Use it to discover what you can query, then pull the data with ` + "`sapb1 query <Entity>`" + `.`,
		Example: exampleBlock(
			`sapb1 entities`,
			`sapb1 entities --search invoice`,
			`sapb1 entities --read-only`,
			`sapb1 entities --search order --json`,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			svcs := filterServices(catalog.Services(), search, readOnly)
			if flagJSON {
				return renderJSONValue(cmd.OutOrStdout(), entitiesJSON(svcs))
			}
			renderEntitiesTable(cmd.OutOrStdout(), svcs)
			return nil
		},
	}

	cmd.Flags().StringVar(&search, "search", "", "case-insensitive substring filter on the service/entity name")
	cmd.Flags().BoolVar(&readOnly, "read-only", false, "only services that are readable (expose a GET)")
	return cmd
}

func filterServices(all []catalog.Service, search string, readOnly bool) []catalog.Service {
	search = strings.ToLower(strings.TrimSpace(search))
	var out []catalog.Service
	for _, s := range all {
		if readOnly && !s.IsReadable() {
			continue
		}
		if search != "" && !strings.Contains(strings.ToLower(s.Service), search) {
			continue
		}
		out = append(out, s)
	}
	return out
}

func renderEntitiesTable(w io.Writer, svcs []catalog.Service) {
	if len(svcs) == 0 {
		fmt.Fprintln(w, "(no matching services)")
		return
	}
	tw := tabwriter.NewWriter(w, 0, 2, 2, ' ', 0)
	fmt.Fprintln(tw, "SERVICE\tOPS\tMETHODS\tREADABLE")
	for _, s := range svcs {
		fmt.Fprintf(tw, "%s\t%d\t%s\t%s\n",
			s.Service,
			len(s.Operations),
			strings.Join(s.Methods(), ","),
			yesNo(s.IsReadable()),
		)
	}
	tw.Flush()
	fmt.Fprintf(w, "\n%d service(s).\n", len(svcs))
}

func yesNo(b bool) string {
	if b {
		return "yes"
	}
	return "no"
}

// entitiesJSON is the JSON shape for `entities --json`.
func entitiesJSON(svcs []catalog.Service) []map[string]interface{} {
	out := make([]map[string]interface{}, 0, len(svcs))
	for _, s := range svcs {
		out = append(out, map[string]interface{}{
			"service":  s.Service,
			"ops":      len(s.Operations),
			"methods":  s.Methods(),
			"readable": s.IsReadable(),
		})
	}
	return out
}

// newOpsCmd shows all operations for one service/entity from the catalog.
func newOpsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "ops <ServiceOrEntity>",
		Short: "Show all catalogued operations for one service/entity (offline)",
		Long: `ops prints every operation (HTTP method + name) that the embedded catalog
records for a service or entity. The match is case-insensitive; if there is no
exact match, the closest names are suggested. Fully offline.

Note: sapb1 is read-only. Write operations (POST/PUT/PATCH/DELETE) are shown
for reference only — the CLI never executes them.`,
		Example: exampleBlock(
			`sapb1 ops Orders`,
			`sapb1 ops OrdersService`,
			`sapb1 ops BusinessPartners --json`,
		),
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			name := strings.TrimSpace(args[0])
			if name == "" {
				return &errs.UsageError{Msg: "a service or entity name is required, e.g. `sapb1 ops Orders`"}
			}
			svc, ok := catalog.Find(name)
			if !ok {
				return unknownEntityError(name)
			}
			if flagJSON {
				return renderJSONValue(cmd.OutOrStdout(), opsJSON(svc))
			}
			renderOpsTable(cmd.OutOrStdout(), svc)
			return nil
		},
	}
	return cmd
}

func renderOpsTable(w io.Writer, svc catalog.Service) {
	fmt.Fprintf(w, "%s  (readable: %s)\n\n", svc.Service, yesNo(svc.IsReadable()))
	if len(svc.Operations) == 0 {
		fmt.Fprintln(w, "(no operations)")
		return
	}
	tw := tabwriter.NewWriter(w, 0, 2, 2, ' ', 0)
	fmt.Fprintln(tw, "METHOD\tNAME")
	for _, op := range svc.Operations {
		fmt.Fprintf(tw, "%s\t%s\n", strings.ToUpper(op.Method), op.Name)
	}
	tw.Flush()
	fmt.Fprintf(w, "\n%d operation(s).\n", len(svc.Operations))
}

func opsJSON(svc catalog.Service) map[string]interface{} {
	ops := make([]map[string]string, 0, len(svc.Operations))
	for _, op := range svc.Operations {
		ops = append(ops, map[string]string{"method": op.Method, "name": op.Name})
	}
	return map[string]interface{}{
		"service":    svc.Service,
		"readable":   svc.IsReadable(),
		"operations": ops,
	}
}

// newCatalogCmd is the parent for catalog-wide subcommands (currently `stats`).
func newCatalogCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "catalog",
		Short: "Inspect the embedded Service Layer catalog (offline)",
	}
	cmd.AddCommand(newCatalogStatsCmd())
	return cmd
}

func newCatalogStatsCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "stats",
		Short: "Print totals over the embedded catalog (services, ops, methods, readable)",
		Example: exampleBlock(
			`sapb1 catalog stats`,
			`sapb1 catalog stats --json`,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			st := catalog.ComputeStats()
			if flagJSON {
				return renderJSONValue(cmd.OutOrStdout(), st)
			}
			renderStats(cmd.OutOrStdout(), st)
			return nil
		},
	}
}

func renderStats(w io.Writer, st catalog.Stats) {
	fmt.Fprintf(w, "Services:            %d\n", st.Services)
	fmt.Fprintf(w, "Operations:          %d\n", st.Operations)
	fmt.Fprintf(w, "Readable (has GET):  %d\n", st.Readable)
	fmt.Fprintln(w, "\nBy HTTP method:")
	tw := tabwriter.NewWriter(w, 0, 2, 2, ' ', 0)
	// Canonical methods first, then any others the catalog happens to contain.
	printed := map[string]bool{}
	for _, m := range catalog.MethodOrder() {
		if n, ok := st.ByMethod[m]; ok {
			fmt.Fprintf(tw, "  %s\t%d\n", m, n)
			printed[m] = true
		}
	}
	var rest []string
	for m := range st.ByMethod {
		if !printed[m] {
			rest = append(rest, m)
		}
	}
	sort.Strings(rest)
	for _, m := range rest {
		fmt.Fprintf(tw, "  %s\t%d\n", m, st.ByMethod[m])
	}
	tw.Flush()
}

// newFieldsCmd discovers the real field names of a live entity, with an
// offline catalog fallback.
func newFieldsCmd() *cobra.Command {
	cmd := &cobra.Command{
		Use:   "fields <Entity>",
		Short: "Discover an entity's real field names (live GET ?$top=1, offline fallback to catalog)",
		Long: `fields answers "what can I --select?". Live, it does a GET <Entity>?$top=1 and
lists the JSON keys of the first record (sorted). If SAP is unreachable or not
configured, it falls back to showing the entity's operations from the embedded
catalog so you still get something useful offline.`,
		Example: exampleBlock(
			`sapb1 fields Orders`,
			`sapb1 fields BusinessPartners --json`,
		),
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runFields(cmd, strings.TrimSpace(args[0]))
		},
	}
	return cmd
}

func runFields(cmd *cobra.Command, entity string) error {
	if entity == "" {
		return &errs.UsageError{Msg: "an entity name is required, e.g. `sapb1 fields Orders`"}
	}

	cfg, err := loadConfig(cmd)
	if err != nil {
		return err
	}

	out := cmd.OutOrStdout()

	// Try the live path only if we have enough config to attempt a request.
	if cfg.ValidateConnection() == nil && cfg.ValidateCompanyDB() == nil {
		c := client.New(cfg)
		res, qErr := c.Query(cmd.Context(), entity, client.QueryOptions{Top: 1})
		if qErr == nil {
			return renderFields(out, entity, res, cfg.JSON)
		}
		// Only a network/unreachability failure falls back to the catalog;
		// auth/API errors are surfaced so the user can fix them.
		var netErr *errs.NetworkError
		if !errors.As(qErr, &netErr) {
			return qErr
		}
		fmt.Fprintf(out, "note: couldn't reach SAP (%s) — falling back to the embedded catalog.\n\n", netErr.Msg)
	} else {
		fmt.Fprintln(out, "note: SAP connection not configured — showing the entity's catalogued operations instead.")
		fmt.Fprintln(out)
	}

	// Offline fallback: show the entity's catalogued operations.
	svc, ok := catalog.Find(entity)
	if !ok {
		return unknownEntityError(entity)
	}
	renderOpsTable(out, svc)
	return nil
}

// renderFields lists the sorted JSON keys of the first returned record.
func renderFields(w io.Writer, entity string, res *client.QueryResult, asJSON bool) error {
	if len(res.Value) == 0 {
		if asJSON {
			return renderJSONValue(w, []string{})
		}
		fmt.Fprintf(w, "%s returned no rows — cannot infer fields (the entity may be empty).\n", entity)
		return nil
	}
	keys := make([]string, 0, len(res.Value[0]))
	for k := range res.Value[0] {
		keys = append(keys, k)
	}
	sort.Strings(keys)

	if asJSON {
		return renderJSONValue(w, keys)
	}
	fmt.Fprintf(w, "%s fields (%d):\n", entity, len(keys))
	for _, k := range keys {
		fmt.Fprintf(w, "  %s\n", k)
	}
	return nil
}

// unknownEntityError builds a usage error (exit 2) with "did you mean?" hints.
func unknownEntityError(name string) error {
	msg := fmt.Sprintf("no service or entity named %q in the catalog", name)
	if sugg := catalog.Suggest(name, maxSuggestions); len(sugg) > 0 {
		msg += " — did you mean: " + strings.Join(sugg, ", ") + "?"
	}
	return &errs.UsageError{Msg: msg}
}
