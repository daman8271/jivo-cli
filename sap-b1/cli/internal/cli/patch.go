package cli

import (
	"fmt"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
)

func newPatchCmd() *cobra.Command {
	var wf writeFlags
	var key string

	cmd := &cobra.Command{
		Use:   "patch <Entity(key)>",
		Short: "Update fields on one existing SAP object (PATCH)",
		Long: `patch updates fields on a single existing object, addressed by its key.

Only the fields in your JSON are changed; everything else is left alone (that's
what PATCH means). The change is live as soon as SAP accepts it, and this CLI
cannot undo it — so patch narrow, and patch things that are safe to change
(remarks, contact details, a reference field), not the numbers on a posted
document. SAP itself will refuse most edits to closed/posted documents.

Address the object either way:

  sapb1 patch "BusinessPartners('V10000')" --data '{"Phone1":"9876543210"}'
  sapb1 patch BusinessPartners --key V10000 --data '{"Phone1":"9876543210"}'

Both spellings are parsed and rebuilt — never forwarded as typed — so the entity
must be a bare, catalogued, PATCH-able entity set, and a key containing "/", "#",
"%" or a space is percent-encoded correctly (JIVO item codes like OIL/1L/MUS
depend on that). Query strings, action paths and trailing junk are refused. Whether
a key is quoted is decided by the entity, not by how the key looks: CardCode
"200001" is a string key, so it becomes BusinessPartners('200001').

A successful PATCH normally returns HTTP 204 with no body. Use --dry-run to see
the exact request without sending it; otherwise the request is previewed and
confirmed (or pass --yes), and every attempt is appended to the write log
(~/.sapb1-writes.jsonl, or $SAPB1_WRITE_LOG).`,
		Example: exampleBlock(
			`sapb1 patch "BusinessPartners('V10000')" --data '{"Phone1":"9876543210"}'`,
			`sapb1 patch BusinessPartners --key V10000 --data '{"EmailAddress":"ap@vendor.com"}'`,
			`sapb1 patch Items --key "OIL/1L/MUS" --dry-run --data '{"ItemName":"Mustard Oil 1L"}'`,
			`sapb1 patch Orders --key 123 --data '{"Comments":"customer moved delivery to Monday"}' --yes`,
		),
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runPatch(cmd, args[0], key, wf)
		},
	}

	cmd.Flags().StringVar(&key, "key", "", "the key of the object to update, when the argument is a bare entity set name")
	addWriteFlags(cmd, &wf)
	return cmd
}

func runPatch(cmd *cobra.Command, target, key string, wf writeFlags) error {
	cfg, err := writeConfig(cmd)
	if err != nil {
		return err
	}

	// Validation and encoding happen before the payload is even read, so a bad
	// target never opens a session.
	path, err := resolvePatchPath(target, key)
	if err != nil {
		return err
	}

	payload, _, err := loadPayload(cmd, wf)
	if err != nil {
		return err
	}

	if wf.dryRun {
		return renderDryRun(cmd, cfg, "PATCH", path, payload)
	}

	if err := confirmWrite(cmd, cfg, "PATCH", path, payload, wf.yes, stdinIsTTYFunc()); err != nil {
		return err
	}

	c := client.New(cfg)
	c.SetErrWriter(cmd.ErrOrStderr())
	res, err := c.Update(cmd.Context(), path, payload)
	if err != nil {
		return err
	}

	return renderWriteResult(cmd.OutOrStdout(), res, cfg.JSON, func(updated map[string]interface{}) string {
		if updated == nil {
			return fmt.Sprintf("Updated %s in %s (HTTP %d).", path, cfg.CompanyDB, res.Status)
		}
		if keys := describeKeys(updated); keys != "" {
			return fmt.Sprintf("Updated %s in %s: %s.", path, cfg.CompanyDB, keys)
		}
		return fmt.Sprintf("Updated %s in %s.", path, cfg.CompanyDB)
	})
}
