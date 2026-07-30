package main

import "github.com/spf13/cobra"

// sectionRegistrars is populated by each cmd_<section>.go via init(). newRootCmd
// ranges over it, so section files can be added or regenerated without touching
// root.go.
var sectionRegistrars []func(*App) *cobra.Command

func registerSection(f func(*App) *cobra.Command) {
	sectionRegistrars = append(sectionRegistrars, f)
}
