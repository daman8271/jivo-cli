package cli

import (
	"encoding/json"
	"fmt"
	"strings"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
	"sapb1/internal/errs"
)

// fifoLayersOp is the single service operation this command may call. It is
// spelled out here and checked again in internal/client against its own
// allowlist, so widening one place alone changes nothing.
// locTypeWarehouse is OIVL.LocType for a warehouse. Sending LocationType null
// instead returns an empty layer list with a 200, so this is the default.
const locTypeWarehouse = 64

const fifoLayersOp = "MaterialRevaluationFIFOService_GetMaterialRevaluationFIFO"

// boolToTYesNo renders a Go bool the way the Service Layer spells one.
func boolToTYesNo(b bool) string {
	if b {
		return "tYES"
	}
	return "tNO"
}

func newFIFOLayersCmd() *cobra.Command {
	var (
		warehouse    string
		locationType int
		showIssued   bool
		rawParams    string
	)

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
allowlist in internal/client with a test over it.

Reading the layers is all this does. Creating the Inventory Revaluation that
acts on them is a POST of MaterialRevaluation, which ` + "`sapb1 post`" + ` refuses as a
posting document, and which has no draft form — SAP's Drafts table holds
marketing documents only. That document is keyed by a human in the SAP B1
client.`,
		Example: exampleBlock(
			`sapb1 fifo-layers FG0000260 --warehouse BH-FG --company JIVO_BEVERAGES_HANADB`,
			`sapb1 fifo-layers PM0000707 --warehouse BH-PP --json`,
			`sapb1 fifo-layers FG0000260 --params '{"ItemCode":"FG0000260","LocationCode":"BH-FG","LocationType":64}'`,
		),
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			return runFIFOLayers(cmd, args[0], warehouse, locationType, showIssued, rawParams)
		},
	}

	cmd.Flags().StringVar(&warehouse, "warehouse", "", "warehouse code — sent as LocationCode, e.g. BH-FG")
	cmd.Flags().IntVar(&locationType, "location-type", locTypeWarehouse, "LocationType: 64 = warehouse (the default). 0 sends null, which returns an EMPTY list")
	cmd.Flags().BoolVar(&showIssued, "show-issued", false, "also return layers already fully issued (ShowIssuedLayers)")
	cmd.Flags().StringVar(&rawParams, "params", "", "raw JSON for MaterialRevaluationFIFOParams, used INSTEAD of the flags above")
	return cmd
}

func runFIFOLayers(cmd *cobra.Command, itemCode, warehouse string, locationType int, showIssued bool, rawParams string) error {
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

	// The parameter names come from SAP's own Service Layer reference, which ships
	// in this repo at sap-b1/api-reference/raw/service-layer-api-reference.html:
	//
	//     { "MaterialRevaluationFIFOParams": {
	//         "ItemCode": "I001", "LocationCode": null,
	//         "LocationType": null, "ShowIssuedLayers": "tNO" } }
	//
	// It is LocationCode, not WarehouseCode — the latter is the spelling used on a
	// MaterialRevaluation LINE, and sending it here is refused with
	// "[SAP -1000] Property 'WarehouseCode' of 'MaterialRevaluationFIFOParams' is invalid".
	//
	// LocationType MUST be 64 (warehouse). SAP's published example leaves it null,
	// and null is the trap: the call still returns 200 with an EMPTY Layers array,
	// which reads as "nothing to revalue" when there is plenty. Verified live on
	// JIVO_BEVERAGES_HANADB, 2026-09-19 — PM0000694 in BH-PM returns 0 layers with
	// null and 9 layers with 64. Pass --location-type 0 to send null deliberately.
	//
	// --params overrides all of it. That escape hatch exists so a shape SAP wants
	// but this command does not build costs an operator one flag, not a rebuild.
	var params interface{}
	if strings.TrimSpace(rawParams) != "" {
		if err := json.Unmarshal([]byte(rawParams), &params); err != nil {
			return &errs.UsageError{Msg: fmt.Sprintf("--params is not valid JSON: %v", err)}
		}
	} else {
		if strings.TrimSpace(warehouse) == "" {
			return &errs.UsageError{Msg: "--warehouse is required (or pass the whole parameter object with --params)"}
		}
		p := map[string]interface{}{
			"ItemCode":         itemCode,
			"LocationCode":     warehouse,
			"LocationType":     locationType,
			"ShowIssuedLayers": boolToTYesNo(showIssued),
		}
		if locationType == 0 {
			p["LocationType"] = nil
		}
		params = p
	}

	payload, err := json.Marshal(map[string]interface{}{"MaterialRevaluationFIFOParams": params})
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

	// SAP returns the rows under "Layers", not the OData "value" this CLI sees
	// everywhere else — this operation is a service call, not an entity set.
	// "value" is kept as a fallback in case a future Service Layer normalises it.
	var parsed struct {
		Layers []map[string]interface{} `json:"Layers"`
		Value  []map[string]interface{} `json:"value"`
	}
	if err := json.Unmarshal(body, &parsed); err != nil || (parsed.Layers == nil && parsed.Value == nil) {
		// Shape not as expected — hand back what SAP said rather than guess.
		_, err := fmt.Fprintln(out, string(body))
		return err
	}
	rows := parsed.Layers
	if rows == nil {
		rows = parsed.Value
	}

	if len(rows) == 0 {
		fmt.Fprintf(out, "No revaluable FIFO layers for %s in %s (%s).\n", itemCode, warehouse, cfg.CompanyDB)
		if locationType == 0 {
			fmt.Fprintln(out, "Note: --location-type 0 sent LocationType null, which returns an empty list even when layers exist. Retry without it.")
		}
		return nil
	}

	// Field names read off a live response, not guessed:
	// TransactionSequenceNum, LayerID, DocNumber, DocType, EntryDate, CurrentCost, OpenQty.
	cols := []string{"TransactionSequenceNum", "LayerID", "DocNumber", "DocType", "EntryDate", "CurrentCost", "OpenQty"}
	renderTable(out, rows, cols)
	return nil
}
