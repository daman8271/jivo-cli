// Command jivodist builds JIVO distribution bundles: a zip of the CLIs a
// colleague needs, with their live credentials already in the right places.
//
//	jivodist                                     # serve the UI on 127.0.0.1:7788
//	jivodist -selection sel.json -o out.zip      # build one bundle, print the result
//	jivodist -list                               # what can be bundled, per target
//
// Every zip it produces contains production credentials. They are written only
// into distribution/dist/, which the tool refuses to use unless git ignores it.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"jivodist/internal/engine"
	"jivodist/internal/httpapi"
	"jivodist/internal/manifest"
)

func main() {
	log.SetFlags(0)
	log.SetPrefix("jivodist: ")

	var (
		serve       = flag.Bool("serve", false, "run the web UI (the default when no other mode is given)")
		addr        = flag.String("addr", httpapi.DefaultAddr, "address to listen on")
		repo        = flag.String("repo", "", "path to the jivo-cli checkout (default: walk up from the working directory)")
		selection   = flag.String("selection", "", "build one bundle from this selection JSON file")
		out         = flag.String("o", "", "output zip path for -selection (default: distribution/dist/<generated name>)")
		list        = flag.Bool("list", false, "print components and their availability as JSON")
		keepStaging = flag.Bool("keep-staging", false, "keep the staged tree under distribution/staging for debugging")
	)
	flag.Parse()

	repoRoot, err := findRepo(*repo)
	if err != nil {
		log.Fatal(err)
	}

	switch {
	case *list && !*serve:
		err = runList(repoRoot)
	case *selection != "" && !*serve:
		err = runBuild(repoRoot, *selection, *out, *keepStaging)
	default:
		err = runServe(repoRoot, *addr)
	}
	if err != nil {
		log.Fatal(err)
	}
}

func findRepo(flagValue string) (string, error) {
	start := flagValue
	if start == "" {
		wd, err := os.Getwd()
		if err != nil {
			return "", err
		}
		start = wd
	}
	root, err := manifest.FindRepoRoot(start)
	if err != nil {
		return "", fmt.Errorf("%w (pass -repo /path/to/jivo-cli)", err)
	}
	return root, nil
}

func runList(repoRoot string) error {
	home, _ := os.UserHomeDir()
	view, err := httpapi.BuildManifestView(repoRoot, home, time.Now())
	if err != nil {
		return err
	}
	return printJSON(view)
}

// runBuild is the verification seam: the same engine.Build the API calls, with
// its Result printed to stdout so a test or a person can check it.
func runBuild(repoRoot, selectionPath, outPath string, keepStaging bool) error {
	raw, err := os.ReadFile(selectionPath)
	if err != nil {
		return err
	}
	var sel engine.Selection
	if err := json.Unmarshal(raw, &sel); err != nil {
		return fmt.Errorf("%s: %w", selectionPath, err)
	}

	if outPath != "" {
		abs, err := absFromCwd(outPath)
		if err != nil {
			return err
		}
		outPath = abs
	}

	res, err := engine.Build(repoRoot, sel, engine.Options{OutPath: outPath, KeepStaging: keepStaging})
	if err != nil {
		return err
	}
	if err := printJSON(res); err != nil {
		return err
	}
	for _, w := range res.Warnings {
		fmt.Fprintln(os.Stderr, "warning: "+w)
	}
	return nil
}

func runServe(repoRoot, addr string) error {
	srv := httpapi.New(repoRoot)
	srv.Addr = addr // defines the Host allowlist; must match what we listen on

	// Fail fast rather than on the first build: if the output directory is
	// committable, nothing here should run at all.
	if err := engine.AssertIgnored(repoRoot, engine.GuardedOutputDirs...); err != nil {
		return err
	}

	log.Printf("repo   %s", repoRoot)
	log.Printf("listen http://%s", addr)
	log.Printf("bundles are written to %s/%s and are NEVER committed", repoRoot, engine.DistDir)

	httpServer := &http.Server{
		Addr:              addr,
		Handler:           srv.Routes(),
		ReadHeaderTimeout: 10 * time.Second,
	}
	return httpServer.ListenAndServe()
}

// absFromCwd resolves -o against the working directory, not the repo root, so
// `jivodist -o dist/test.zip` means what the person typing it expects.
func absFromCwd(p string) (string, error) { return filepath.Abs(p) }

func printJSON(v any) error {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(v)
}
