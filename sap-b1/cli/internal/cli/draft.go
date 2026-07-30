package cli

import (
	"fmt"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
	"sapb1/internal/errs"
)

func newDraftCmd() *cobra.Command {
	var wf writeFlags

	cmd := &cobra.Command{
		Use:   "draft <doctype>",
		Short: "Create a DRAFT document in SAP (the intended write path)",
		Long: `draft creates a document in SAP's Drafts table instead of posting it live.

This is the write path this tool is built around. A draft is not a posted
document: it does not touch stock, it does not hit the ledger, and it does not
become real until a human opens SAP B1 (Sales/Purchasing → Document Drafts),
reviews it, and presses Add. Nothing here can be un-added by the CLI, so the
safe move is always to draft it and let a person do the posting.

Drafts ARE visible in SAP — to anyone looking at Document Drafts, and to the
approval workflow if one is configured for that document type. Treat a draft as
"submitted for review", not as invisible scratch space.

The document type decides what the draft will become. Any of these forms works
(case-insensitive): the friendly name, the OData entity set, the oXxx enum, or
the numeric object type.

  NAME                   ENTITY SET             ENUM
` + docTypeTable() + `

Your payload goes out byte for byte as you wrote it, with DocObjectCode spliced
in if you left it out. Use --dry-run to see the exact request without sending
anything. Otherwise the write is previewed and confirmed (or pass --yes), and
every attempt is appended to the write log (~/.sapb1-writes.jsonl, or
$SAPB1_WRITE_LOG).`,
		Example: exampleBlock(
			`sapb1 draft order --data '{"CardCode":"C0001","DocumentLines":[{"ItemCode":"A0001","Quantity":10}]}'`,
			`sapb1 draft order --dry-run --data '{"CardCode":"C0001"}'   # show it, send nothing`,
			`sapb1 draft purchase-order --company JIVO_MART_HANADB \`,
			`  --data '{"CardCode":"V10000","DocumentLines":[{"ItemCode":"A0001","Quantity":100}]}'`,
			`sapb1 draft invoice --data-file draft-invoice.json --yes --json`,
			`cat draft-order.json | sapb1 draft order --data-file - --yes`,
		),
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runDraft(cmd, args[0], wf)
		},
	}

	addWriteFlags(cmd, &wf)
	return cmd
}

func runDraft(cmd *cobra.Command, docTypeArg string, wf writeFlags) error {
	cfg, err := writeConfig(cmd)
	if err != nil {
		return err
	}

	objectCode, err := resolveDocObjectCode(docTypeArg)
	if err != nil {
		return err
	}

	payload, obj, err := loadPayload(cmd, wf)
	if err != nil {
		return err
	}

	// DocObjectCode is what makes a Draft "a draft OF something". Inject it when
	// the payload doesn't say, accept it when it agrees, and refuse when the
	// payload and the command line disagree — that combination is always a
	// mistake, and guessing which one the operator meant is not our call.
	//
	// The check runs against the decoded copy; the WIRE payload is only ever the
	// operator's own bytes, with the field spliced in when it was missing.
	if raw, ok := obj["DocObjectCode"]; ok && raw != nil {
		given := formatCell(raw)
		inPayload, err := resolveDocObjectCode(given)
		if err != nil {
			return &errs.UsageError{Msg: fmt.Sprintf("payload has DocObjectCode %q, which is not a document type I recognize: %v", given, err)}
		}
		if inPayload != objectCode {
			return &errs.UsageError{Msg: fmt.Sprintf("document type mismatch: you asked for %s (%s) but the payload says DocObjectCode %q (%s) — drop one of them",
				docTypeArg, objectCode, given, inPayload)}
		}
		// It agrees — leave the operator's bytes completely alone.
	} else {
		if payload, err = spliceJSONField(payload, "DocObjectCode", objectCode); err != nil {
			return err
		}
	}

	if wf.dryRun {
		return renderDryRun(cmd, cfg, "POST", "Drafts", payload)
	}

	if err := confirmWrite(cmd, cfg, "POST", "Drafts", payload, wf.yes, stdinIsTTYFunc()); err != nil {
		return err
	}

	c := client.New(cfg)
	c.SetErrWriter(cmd.ErrOrStderr())
	res, err := c.Create(cmd.Context(), "Drafts", payload)
	if err != nil {
		return err
	}

	summary := func(created map[string]interface{}) string {
		keys := describeKeys(created)
		if keys == "" {
			keys = fmt.Sprintf("HTTP %d", res.Status)
		}
		return fmt.Sprintf("Draft created in %s: %s (%s). Open SAP B1 → Document Drafts → review → Add.",
			cfg.CompanyDB, keys, objectCode)
	}

	// In --json mode stdout is SAP's object, so the instruction that actually
	// matters — a human still has to Add this in SAP — goes to stderr instead of
	// being dropped.
	if cfg.JSON {
		fmt.Fprintln(cmd.ErrOrStderr(), summary(decodeWriteObject(res.Body)))
	}

	return renderWriteResult(cmd.OutOrStdout(), res, cfg.JSON, summary)
}
