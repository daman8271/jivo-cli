package main

import (
	"github.com/spf13/cobra"
)

// profile — the registration's own master data: legal name, trade name,
// registration date, constitution, jurisdictions, principal address, authorised
// signatory. It is the source for the state_code and the legal name in the
// comparison envelope.
//
// This is a POST because the portal made it one — the body is a literal `{}`,
// there is no GET, and the allowlist row permits no body keys at all. It is the
// third and last POST in this binary.
//
// It carries PII (`contacted{name, mobNum, email}`). The CLI prints what the
// portal returned, as every read here does, but this is the one command whose
// output should not be pasted into a ticket.

func init() { registerSection(newProfileCmd) }

func newProfileCmd(app *App) *cobra.Command {
	return &cobra.Command{
		Use:   "profile",
		Short: "Registration master data: legal name, status, jurisdictions, address, signatory",
		Args:  cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			reg, err := app.one()
			if err != nil {
				return err
			}
			app.logf("note: the profile body contains the authorised signatory's name, mobile and email — do not paste it into a shared ticket.")
			return app.read("profile", reg, epProfile, nil, nil, map[string]any{})
		},
	}
}
