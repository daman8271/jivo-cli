package main

import "github.com/spf13/cobra"

// sectionRegistrars is populated by each cmd_<section>.go via init() →
// registerSection. newRootCmd ranges over it to attach every section command.
// This lets section files be added in parallel WITHOUT any of them editing
// root.go (zero merge conflicts during generation).
var sectionRegistrars []func(*App) *cobra.Command

// registerSection is called from a section file's init() to add its command
// group to the root tree.
func registerSection(f func(*App) *cobra.Command) {
	sectionRegistrars = append(sectionRegistrars, f)
}
