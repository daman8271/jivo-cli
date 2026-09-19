package cli

import (
	"encoding/json"
	"fmt"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
)

// fifoLayersOp is the single service operation this command may call. It is
// spelled out here and checked again in internal/client against its own
// allowlist, so widening one place alone changes nothing.
const fifoLayersOp = "MaterialRevaluationFIFOService_GetMaterialRevaluationFIFO"

func newFIFOLayersCmd() *cobra.Command {
	var warehouse string

	cmd := &cobra.Command{
		Use:   "fifo-layers <ItemCode>",
		Short: "List the FIFO cost layers a revaluation may target (read-only)",
		Long: `fifo-layers shows the FIFO valuation layers SAP will let an Inventory
Revaluation act on, for one item and warehouse.

This is a READ. It changes nothing, it is not previewed or confirmed, and it is
not written to the write log, because there is nothing to undo.

It exists because the layer state cannot be derived from the tables. ` + "`OIVL`" + `
carries the movements — ` + "`SUM(InQty - OutQty)`" + ` ties to ` + "`OITW.OnHand`" + ` on every
item — but ` + "`OIVL.OpenQty`" + ` is not the remaining layer, and reading it that way
overstates on-hand on items that have never been near a disassembly order. SAP
computes the revaluable layers itself and exposes them only through this call.

The layer's TransactionSequenceNum is what a MaterialRevaluation payload puts in
` + "`MaterialRevaluationLines[].FIFOLayers[].TransactionSequenceNum`" + `. Those
sequence numbers come from ` + "`OIVL`" + `, NOT from ` + "`OINM`" + ` — the two tables number
independently, and an OINM sequence is rejected with a bare -5002.

Only this one service operation is reachable. Every other Service Layer action —
MaterialRevaluation(id)/Cancel, MaterialRevaluation(id)/Close,
Drafts(id)/SaveDraftToDocument, Orders(id)/Close — stays refused, by an exact-match
allowlist in internal/client with a test over it.`,
		Example: exampleBlock(
			`sapb1 fifo-layers FG0000260 --warehouse BH-FG --company JIVO_BEVERAGES_HANADB`,
			`sapb1 fifo-layers PM0000707 --warehouse BH-PP --json`,
		),
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runFIFOLayers(cmd, args[0], warehouse)
		},
	}

	cmd.Flags().StringVar(&warehouse, "warehouse", "", "warehouse code (required), e.g. BH-FG")
	_ = cmd.MarkFlagRequired("warehouse")
	return cmd
}

func runFIFOLayers(cmd *cobra.Command, itemCode, warehouse string) error {
	cfg, err := loadConfig(cmd)
	if err != nil {
		return err
	}
	if err := cfg.ValidateConnection(); err != nil {
		return err
	}
	if err := cfg.ValidateCompanyDB(); err != nil {
		return err
	}

	payload, err := json.Marshal(map[string]interface{}{
		"MaterialRevaluationFIFOParams": map[string]interface{}{
			"ItemCode":      itemCode,
			"WarehouseCode": warehouse,
		},
	})
	if err != nil {
		return err
	}

	c := client.New(cfg)
	c.SetErrWriter(cmd.ErrOrStderr())
	body, err := c.CallReadService(cmd.Context(), fifoLayersOp, payload)
	if err != nil {
		return err
	}

	out := cmd.OutOrStdout()
	if cfg.JSON {
		_, err := fmt.Fprintln(out, string(body))
		return err
	}

	var parsed struct {
		Value []map[string]interface{} `json:"value"`
	}
	if err := json.Unmarshal(body, &parsed); err != nil || parsed.Value == nil {
		// Shape not as expected — hand back what SAP said rather than guess.
		_, err := fmt.Fprintln(out, string(body))
		return err
	}

	if len(parsed.Value) == 0 {
		fmt.Fprintf(out, "No revaluable FIFO layers for %s in %s (%s).\n", itemCode, warehouse, cfg.CompanyDB)
		return nil
	}

	cols := []string{"TransactionSequenceNum", "LayerID", "Quantity", "Price", "LineTotal", "BaseLine"}
	renderTable(out, parsed.Value, cols)
	return nil
}
