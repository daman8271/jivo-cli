//go:build !readonly

package cli

import (
	"fmt"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
)

func newPostCmd() *cobra.Command {
	var wf writeFlags

	cmd := &cobra.Command{
		Use:   "post <EntitySet>",
		Short: "Create an object directly in SAP (no draft) — prefer `draft` for documents",
		Long: `post creates an object in SAP by POSTing your JSON to an entity set directly.

This is the escape hatch, not the front door. For any marketing document
(order, invoice, delivery, purchase order, credit note, …) use ` + "`sapb1 draft`" + `
instead: a draft waits for a human to review and Add it, whereas a document
posted here is live the moment SAP accepts it — it hits stock and the ledger,
and this CLI cannot delete or cancel it.

Where post earns its keep is master data and other non-posting objects that
have no draft equivalent, e.g.:

  sapb1 post BusinessPartners   — a new customer/vendor
  sapb1 post Items              — a new item
  sapb1 post ProjectCodes, ItemGroups, ...

The argument must be a BARE entity-set name that the embedded catalog knows and
that accepts a POST. Anything else is refused, which specifically means OData
ACTIONS are not available here: Invoices(9)/Cancel, Orders(1)/Close,
Drafts(4321)/SaveDraftToDocument and friends are all POSTs, and they are exactly
the irreversible steps this tool leaves to a human in the SAP B1 client. There is
no flag to override that.

The payload is one JSON object matching the entity's own field names — the same
names ` + "`sapb1 fields <Entity>`" + ` lists — and is sent byte for byte as you
wrote it. Use --dry-run to see the exact request without sending it; otherwise
the request is previewed and confirmed (or pass --yes), and every attempt is
appended to the write log (~/.sapb1-writes.jsonl, or $SAPB1_WRITE_LOG).`,
		Example: exampleBlock(
			`sapb1 post BusinessPartners --data '{"CardCode":"C90001","CardName":"Test Customer","CardType":"cCustomer"}'`,
			`sapb1 post Items --data-file new-item.json --dry-run`,
			`sapb1 post BusinessPartners --data-file bp.json --yes --company JIVO_MART_HANADB`,
		),
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runPost(cmd, args[0], wf)
		},
	}

	addWriteFlags(cmd, &wf)
	return cmd
}

func runPost(cmd *cobra.Command, entitySetArg string, wf writeFlags) error {
	cfg, err := writeConfig(cmd)
	if err != nil {
		return err
	}

	// Bare, catalogued, POST-able entity sets only — no action paths, no
	// hand-built OData. Runs before anything else so a rejected target never
	// even reads the payload, let alone opens a session.
	entitySet, err := validateWriteEntitySet(entitySetArg, "POST")
	if err != nil {
		return err
	}

	payload, _, err := loadPayload(cmd, wf)
	if err != nil {
		return err
	}

	if wf.dryRun {
		return renderDryRun(cmd, cfg, "POST", entitySet, payload)
	}

	if err := confirmWrite(cmd, cfg, "POST", entitySet, payload, wf.yes, stdinIsTTYFunc()); err != nil {
		return err
	}

	c := client.New(cfg)
	c.SetErrWriter(cmd.ErrOrStderr())
	res, err := c.Create(cmd.Context(), entitySet, payload)
	if err != nil {
		return err
	}

	return renderWriteResult(cmd.OutOrStdout(), res, cfg.JSON, func(created map[string]interface{}) string {
		keys := describeKeys(created)
		if keys == "" {
			keys = fmt.Sprintf("HTTP %d", res.Status)
		}
		return fmt.Sprintf("Created %s in %s: %s.", entitySet, cfg.CompanyDB, keys)
	})
}
