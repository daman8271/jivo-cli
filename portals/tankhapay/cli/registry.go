package main

import "github.com/spf13/cobra"

// sectionRegistrars is populated by each generated cmd_<section>.go via init() →
// registerSection. newRootCmd ranges over it to attach every section command, so
// section files add themselves with zero edits to root.go.
var sectionRegistrars []func(*App) *cobra.Command

func registerSection(f func(*App) *cobra.Command) {
	sectionRegistrars = append(sectionRegistrars, f)
}
