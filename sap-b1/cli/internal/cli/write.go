//go:build !readonly

package cli

import (
	"bufio"
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"golang.org/x/term"

	"sapb1/internal/client"
	"sapb1/internal/config"
	"sapb1/internal/errs"
)

// writeFlags backs the --data/--data-file/--yes/--dry-run shape shared by the
// three write commands (`draft`, `post`, `patch`).
type writeFlags struct {
	data     string
	dataFile string
	yes      bool
	dryRun   bool
}

func addWriteFlags(cmd *cobra.Command, wf *writeFlags) {
	cmd.Flags().StringVar(&wf.data, "data", "", "the JSON object to send, inline (mutually exclusive with --data-file)")
	cmd.Flags().StringVar(&wf.dataFile, "data-file", "", "file containing the JSON object to send; \"-\" reads stdin (which then requires --yes)")
	cmd.Flags().BoolVar(&wf.yes, "yes", false, "skip the confirmation prompt — required when stdin is not a terminal")
	cmd.Flags().BoolVar(&wf.dryRun, "dry-run", false, "print the exact request that WOULD be sent, then exit; contacts SAP not at all")
}

// stdinIsTTY reports whether stdin is a terminal, i.e. whether there is a human
// on the other end who could answer a confirmation prompt. It uses a real
// terminal check rather than "is stdin a character device" — /dev/null is a
// character device too, so `< /dev/null` used to look interactive. Indirected
// through stdinIsTTYFunc so tests can drive both paths.
func stdinIsTTY() bool {
	return term.IsTerminal(int(os.Stdin.Fd()))
}

var stdinIsTTYFunc = stdinIsTTY

// writeConfig resolves the effective config for a write command and applies the
// same connection/company checks the read path uses, plus the output-format rules
// that make sense for a write (no --csv: there's no table to emit).
func writeConfig(cmd *cobra.Command) (*config.Config, error) {
	cfg, err := loadConfig(cmd)
	if err != nil {
		return nil, err
	}
	if cfg.CSV {
		return nil, &errs.UsageError{Msg: "--csv is not supported for write commands; use --json to get the created object back as JSON"}
	}
	if err := cfg.ValidateConnection(); err != nil {
		return nil, err
	}
	if err := cfg.ValidateCompanyDB(); err != nil {
		return nil, err
	}
	return cfg, nil
}

// stdinPayloadPaths are the spellings of "read the payload from stdin". Each one
// consumes stdin, which is also where a confirmation would have to be typed — so
// any of them requires --yes (or --dry-run, which sends nothing).
var stdinPayloadPaths = map[string]bool{
	"-":               true,
	"/dev/stdin":      true,
	"/dev/fd/0":       true,
	"/proc/self/fd/0": true,
}

// loadPayload reads the request body from exactly one of --data or --data-file
// ("-" = stdin) and insists it is a single JSON object — one document per call,
// never an array.
//
// It returns the COMPACTED ORIGINAL BYTES (which is what goes on the wire) plus a
// decoded copy for inspection. The decode keeps numbers as json.Number, and the
// decoded map is never re-marshaled back onto the wire, so inspecting a payload
// can't silently reshape a long DocNum or a high-precision total.
func loadPayload(cmd *cobra.Command, wf writeFlags) ([]byte, map[string]interface{}, error) {
	fromStdin := stdinPayloadPaths[strings.TrimSpace(wf.dataFile)]

	switch {
	case wf.data != "" && wf.dataFile != "":
		return nil, nil, &errs.UsageError{Msg: "--data and --data-file are mutually exclusive — pass the JSON one way or the other"}
	case wf.data == "" && wf.dataFile == "":
		return nil, nil, &errs.UsageError{Msg: `no payload given — pass the JSON body with --data '{"CardCode":"C0001"}' or --data-file body.json`}
	case fromStdin && !wf.yes && !wf.dryRun:
		// The payload consumes stdin, so there is nothing left to type "yes" on.
		return nil, nil, &errs.UsageError{Msg: fmt.Sprintf(
			"--data-file %s reads the payload from stdin, which leaves no way to answer the confirmation prompt — add --yes if you really mean this write (or --dry-run to see it first)",
			wf.dataFile)}
	}

	var raw []byte
	switch {
	case wf.data != "":
		raw = []byte(wf.data)
	case fromStdin:
		b, err := io.ReadAll(cmd.InOrStdin())
		if err != nil {
			return nil, nil, &errs.UsageError{Msg: fmt.Sprintf("reading payload from stdin: %v", err)}
		}
		raw = b
	default:
		b, err := os.ReadFile(wf.dataFile)
		if err != nil {
			return nil, nil, &errs.UsageError{Msg: fmt.Sprintf("reading --data-file %q: %v", wf.dataFile, err)}
		}
		raw = b
	}

	if len(bytes.TrimSpace(raw)) == 0 {
		return nil, nil, &errs.UsageError{Msg: "payload is empty — nothing to send"}
	}

	parsed, err := decodeExact(raw)
	if err != nil {
		return nil, nil, &errs.UsageError{Msg: fmt.Sprintf("payload is not valid JSON: %v", err)}
	}
	obj, ok := parsed.(map[string]interface{})
	if !ok {
		return nil, nil, &errs.UsageError{Msg: fmt.Sprintf("payload must be a single JSON object like {\"CardCode\":\"C0001\"}, got %s — one document per command", jsonKindOf(parsed))}
	}

	payload, err := compactJSON(raw)
	if err != nil {
		return nil, nil, err
	}
	return payload, obj, nil
}

// decodeExact unmarshals JSON with numbers left as json.Number, so no value is
// reshaped by a float round-trip, and rejects trailing content after the value.
func decodeExact(raw []byte) (interface{}, error) {
	dec := json.NewDecoder(bytes.NewReader(raw))
	dec.UseNumber()
	var v interface{}
	if err := dec.Decode(&v); err != nil {
		return nil, err
	}
	if dec.More() {
		return nil, fmt.Errorf("unexpected trailing content after the JSON value")
	}
	return v, nil
}

// jsonKindOf names the JSON type of v for error messages.
func jsonKindOf(v interface{}) string {
	switch v.(type) {
	case []interface{}:
		return "a JSON array"
	case string:
		return "a JSON string"
	case json.Number, float64:
		return "a JSON number"
	case bool:
		return "a JSON boolean"
	case nil:
		return "JSON null"
	default:
		return "something else"
	}
}

func compactJSON(raw []byte) ([]byte, error) {
	var buf bytes.Buffer
	if err := json.Compact(&buf, raw); err != nil {
		return nil, &errs.UsageError{Msg: fmt.Sprintf("payload is not valid JSON: %v", err)}
	}
	return buf.Bytes(), nil
}

// spliceJSONField inserts "name":"value" as the first member of a compacted JSON
// object, leaving every other byte exactly as the operator wrote it.
//
// This is how `draft` adds DocObjectCode without re-encoding the payload.
// Re-marshaling a decoded map would alphabetize the keys, collapse duplicates,
// and (before json.Number) round every number through float64 — so a 16+ digit
// DocNum came back changed. The wire bytes must be the operator's bytes.
func spliceJSONField(payload []byte, name, value string) ([]byte, error) {
	trimmed := bytes.TrimSpace(payload)
	if len(trimmed) < 2 || trimmed[0] != '{' || trimmed[len(trimmed)-1] != '}' {
		return nil, &errs.UsageError{Msg: "payload must be a single JSON object"}
	}

	field, err := json.Marshal(name)
	if err != nil {
		return nil, err
	}
	val, err := json.Marshal(value)
	if err != nil {
		return nil, err
	}

	var out bytes.Buffer
	out.WriteByte('{')
	out.Write(field)
	out.WriteByte(':')
	out.Write(val)
	if len(trimmed) > 2 { // i.e. not "{}"
		out.WriteByte(',')
		out.Write(trimmed[1 : len(trimmed)-1])
	}
	out.WriteByte('}')
	return out.Bytes(), nil
}

// confirmWrite prints exactly what is about to be sent (to STDERR, so stdout
// stays clean for the result) and then makes sure a human meant it:
//
//   - --yes: proceed.
//   - no --yes and stdin isn't a terminal (cron, pipe, an agent): refuse.
//   - no --yes and stdin is a terminal: require the word "yes", spelled out.
//
// Only an exact "yes" proceeds. "y" is deliberately NOT accepted: one stray
// keystroke should not be able to commit a production write.
//
// stdinIsTTY is a parameter rather than a call so tests can drive both paths.
func confirmWrite(cmd *cobra.Command, cfg *config.Config, method, path string, payload []byte, yes, stdinIsTTY bool) error {
	errOut := cmd.ErrOrStderr()

	fmt.Fprintln(errOut, "About to WRITE to SAP:")
	fmt.Fprintf(errOut, "  company : %s\n", cfg.CompanyDB)
	fmt.Fprintf(errOut, "  user    : %s\n", cfg.User)
	fmt.Fprintf(errOut, "  request : %s %s%s\n", method, cfg.BaseURL(), path)
	fmt.Fprintf(errOut, "  payload :\n%s\n", indentJSON(payload, "    "))

	if yes {
		return nil
	}

	if !stdinIsTTY {
		return &errs.UsageError{Msg: "refusing to write without confirmation: stdin is not a terminal, so nobody can answer the prompt — re-run with --yes if you really mean this write, or with --dry-run to see exactly what it would send"}
	}

	fmt.Fprintf(errOut, "Type 'yes' to send this write to %s: ", cfg.CompanyDB)
	line, err := bufio.NewReader(cmd.InOrStdin()).ReadString('\n')
	if err != nil && strings.TrimSpace(line) == "" {
		return &errs.UsageError{Msg: "aborted — no confirmation read, nothing was sent to SAP"}
	}
	if strings.TrimSpace(line) == "yes" {
		return nil
	}
	return &errs.UsageError{Msg: `aborted at the confirmation prompt — nothing was sent to SAP (only an exact "yes" proceeds)`}
}

// renderDryRun prints the request that WOULD have been sent, and returns.
// Nothing is contacted — not even Login.
//
// This is the sanctioned flow for an agent: run --dry-run, show the operator the
// exact request, and only if they say go, run the same command with --yes.
func renderDryRun(cmd *cobra.Command, cfg *config.Config, method, path string, payload []byte) error {
	out := cmd.OutOrStdout()
	fullURL := cfg.BaseURL() + path

	if cfg.JSON {
		// Marshaled compact, not indented: `payload` then carries the exact bytes
		// that would go on the wire, which is the whole point of a dry run. (The
		// indenting encoder would reformat the nested payload too.)
		b, err := json.Marshal(struct {
			DryRun    bool            `json:"dryRun"`
			CompanyDB string          `json:"companyDb"`
			Host      string          `json:"host"`
			Port      int             `json:"port"`
			Method    string          `json:"method"`
			URL       string          `json:"url"`
			Payload   json.RawMessage `json:"payload"`
		}{true, cfg.CompanyDB, cfg.Host, cfg.Port, method, fullURL, json.RawMessage(payload)})
		if err != nil {
			return err
		}
		_, err = fmt.Fprintln(out, string(b))
		return err
	}

	fmt.Fprintln(out, "DRY RUN — nothing was sent to SAP.")
	fmt.Fprintf(out, "  company : %s\n", cfg.CompanyDB)
	fmt.Fprintf(out, "  request : %s %s\n", method, fullURL)
	fmt.Fprintf(out, "  payload :\n%s\n", indentJSON(payload, "    "))
	fmt.Fprintln(out, "Re-run the same command with --yes to send it.")
	return nil
}

// indentJSON pretty-prints payload for previews, prefixing every line with
// prefix. json.Indent rewrites whitespace only — numbers and key order survive —
// and if the bytes somehow aren't valid JSON they're shown as-is.
func indentJSON(payload []byte, prefix string) string {
	var buf bytes.Buffer
	if err := json.Indent(&buf, payload, prefix, "  "); err != nil {
		return prefix + string(payload)
	}
	return prefix + buf.String()
}

// writeSummaryFunc renders the human one-line result of a successful write. obj
// is the created/updated object the server returned, or nil when it returned no
// body (HTTP 204).
type writeSummaryFunc func(obj map[string]interface{}) string

// renderWriteResult writes the result of a successful write to stdout.
//
// With --json the response body is emitted VERBATIM (re-indented, which changes
// only whitespace), so nothing SAP said is reshaped on the way through —
// including a body that isn't a JSON object at all. An empty body (HTTP 204)
// becomes {"status":204}. Without --json, the command's one-line summary.
func renderWriteResult(out io.Writer, res *client.WriteResult, asJSON bool, summary writeSummaryFunc) error {
	if asJSON {
		body := bytes.TrimSpace(res.Body)
		if len(body) == 0 {
			return renderJSONValue(out, map[string]interface{}{"status": res.Status})
		}
		var buf bytes.Buffer
		if err := json.Indent(&buf, body, "", "  "); err != nil {
			// Not JSON at all — pass SAP's bytes through untouched.
			_, err := fmt.Fprintln(out, string(body))
			return err
		}
		_, err := fmt.Fprintln(out, buf.String())
		return err
	}

	fmt.Fprintln(out, summary(decodeWriteObject(res.Body)))
	return nil
}

// decodeWriteObject decodes a write response body into an object (numbers kept
// exact), or returns nil when there is no body (204) or it isn't a JSON object.
func decodeWriteObject(body []byte) map[string]interface{} {
	if len(bytes.TrimSpace(body)) == 0 {
		return nil
	}
	v, err := decodeExact(body)
	if err != nil {
		return nil
	}
	obj, ok := v.(map[string]interface{})
	if !ok {
		return nil
	}
	return obj
}

// describeKeys renders the identifying fields of a written object for the
// one-line summary, e.g. "DocEntry 4321, DocNum 99" or "CardCode V10000".
// Returns "" when the object carries none of them.
func describeKeys(obj map[string]interface{}) string {
	if obj == nil {
		return ""
	}
	var parts []string
	for _, k := range []string{"DocEntry", "DocNum", "AbsoluteEntry", "CardCode", "ItemCode", "Code"} {
		if v, ok := obj[k]; ok && v != nil {
			parts = append(parts, k+" "+formatCell(v))
		}
	}
	return strings.Join(parts, ", ")
}