package cli

import (
	"fmt"
	"time"

	"github.com/spf13/cobra"

	"sapb1/internal/client"
	"sapb1/internal/errs"
)

func newDoctorCmd() *cobra.Command {
	return &cobra.Command{
		Use:   "doctor",
		Short: "End-to-end diagnostic: config, network, and login",
		Long: `doctor runs through everything needed for sapb1 to work, in order, and
prints a ✓/✗ checklist with actionable hints:

  1. configuration present (host/user/password/companyDB)
  2. host:port reachable over TCP
  3. Login succeeds against the Service Layer

Use this first when something isn't working.`,
		Example: exampleBlock(
			`sapb1 doctor`,
		),
		Args: cobra.NoArgs,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runDoctor(cmd)
		},
	}
}

func runDoctor(cmd *cobra.Command) error {
	out := cmd.OutOrStdout()
	fmt.Fprintln(out, "sapb1 doctor")
	fmt.Fprintln(out, "============")

	cfg, err := loadConfig(cmd)
	if err != nil {
		fmt.Fprintf(out, "✗ configuration     could not be loaded: %v\n", err)
		return err
	}

	// 1. Configuration.
	var missing []string
	if cfg.Host == "" {
		missing = append(missing, "SAPB1_HOST / --host")
	}
	if cfg.User == "" {
		missing = append(missing, "SAPB1_USER / --user")
	}
	if cfg.Password == "" {
		missing = append(missing, "SAPB1_PASSWORD")
	}
	if cfg.CompanyDB == "" {
		missing = append(missing, "SAPB1_COMPANYDB / --company")
	}

	if len(missing) == 0 {
		fmt.Fprintf(out, "✓ configuration      host=%s port=%d company=%s user=%s password=%s\n",
			cfg.Host, cfg.Port, cfg.CompanyDB, cfg.User, cfg.MaskedPassword())
	} else {
		fmt.Fprintf(out, "✗ configuration      missing: %v\n", missing)
		fmt.Fprintln(out, "  hint: copy .env.example to .env and fill in the missing values, or pass the matching flags.")
		if cfg.CompanyDB == "" {
			fmt.Fprintln(out, "  hint: company database not set — ask your SAP admin for the CompanyDB name.")
		}
	}

	// 2. TCP reachability.
	var reachable bool
	if cfg.Host == "" {
		fmt.Fprintln(out, "✗ network            skipped — no host configured")
	} else {
		// Use a short timeout for the raw TCP probe so `doctor` stays snappy
		// even against a fully firewalled host — no point waiting the full
		// request timeout just to find out a SYN is being dropped. Still
		// honors an explicitly shorter --timeout/SAPB1_TIMEOUT.
		const doctorTCPProbeTimeout = 8 * time.Second
		timeout := doctorTCPProbeTimeout
		if cfgTimeout := time.Duration(cfg.Timeout) * time.Second; cfg.Timeout > 0 && cfgTimeout < timeout {
			timeout = cfgTimeout
		}
		if err := client.CheckTCPReachable(cfg.HostPort(), timeout); err != nil {
			fmt.Fprintf(out, "✗ network            cannot reach %s over TCP\n", cfg.HostPort())
			fmt.Fprintln(out, "  hint: are you on the company VPN, or is your IP whitelisted on the SAP box's firewall?")
		} else {
			reachable = true
			fmt.Fprintf(out, "✓ network            %s is reachable over TCP\n", cfg.HostPort())
		}
	}

	// 3. Login.
	var loginErr error
	switch {
	case len(missing) > 0:
		fmt.Fprintln(out, "✗ login              skipped — fix configuration above first")
		loginErr = &errs.ConfigError{Msg: fmt.Sprintf("missing required config: %v", missing)}
	case !reachable:
		fmt.Fprintln(out, "✗ login              skipped — host is not reachable")
		loginErr = &errs.NetworkError{Msg: fmt.Sprintf("cannot reach SAP Service Layer at %s — are you on the company VPN or is your IP whitelisted?", cfg.HostPort())}
	default:
		c := client.New(cfg)
		if err := c.Login(cmd.Context()); err != nil {
			fmt.Fprintf(out, "✗ login              %v\n", err)
			loginErr = err
		} else {
			fmt.Fprintf(out, "✓ login              connected to %s as %s\n", cfg.CompanyDB, cfg.User)
		}
	}

	fmt.Fprintln(out)
	if len(missing) == 0 && reachable && loginErr == nil {
		fmt.Fprintln(out, "All checks passed — you're good to go. Try `sapb1 orders list`.")
		return nil
	}

	fmt.Fprintln(out, "One or more checks failed — see hints above.")
	if len(missing) > 0 {
		return &errs.ConfigError{Msg: fmt.Sprintf("missing required config: %v", missing)}
	}
	if !reachable {
		return &errs.NetworkError{Msg: fmt.Sprintf("cannot reach SAP Service Layer at %s — are you on the company VPN or is your IP whitelisted?", cfg.HostPort())}
	}
	return loginErr
}
