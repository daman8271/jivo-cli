// Copyright 2026 daman8271 and contributors. Licensed under Apache-2.0. See LICENSE.

package cli

import (
	"bufio"
	"bytes"
	"encoding/json"
	"os"
	"reflect"
	"sort"
	"strings"
	"testing"

	"github.com/spf13/cobra"
)

func TestDiscoverAPIInterfacesUsesEndpointDescendantsNotVisibility(t *testing.T) {
	root := &cobra.Command{Use: "test-cli"}

	visibleResource := &cobra.Command{Use: "visible-resource"}
	visibleResource.AddCommand(testEndpointCommand("list", "visible.list", "/visible"))
	root.AddCommand(visibleResource)

	hiddenResource := &cobra.Command{Use: "hidden-resource", Hidden: true}
	hiddenResource.AddCommand(testEndpointCommand("get", "hidden.get", "/hidden/{id}"))
	root.AddCommand(hiddenResource)

	root.AddCommand(&cobra.Command{Use: "doctor", Hidden: true})
	root.AddCommand(&cobra.Command{Use: "search"})

	got := interfaceNames(discoverAPIInterfaces(root))
	want := []string{"hidden-resource", "visible-resource"}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("discoverAPIInterfaces() = %v, want only endpoint-backed groups %v", got, want)
	}
}

func TestDiscoverAPIEndpointMethodsIncludesNestedCommandPaths(t *testing.T) {
	iface := &cobra.Command{Use: "dashboard"}
	detail := &cobra.Command{Use: "state-sales-detail"}
	detail.AddCommand(testEndpointCommand("cities", "dashboard.state-sales-detail-cities", "/api/dashboard/state-sales/detail/cities"))
	iface.AddCommand(detail)
	iface.AddCommand(testEndpointCommand("summary", "dashboard.summary", "/api/dashboard/summary"))

	got := discoverAPIEndpointMethods(iface)
	want := []apiEndpointMethod{
		{
			Name:     "state-sales-detail cities",
			Short:    "test endpoint",
			Endpoint: "dashboard.state-sales-detail-cities",
			Method:   "GET",
			Path:     "/api/dashboard/state-sales/detail/cities",
		},
		{
			Name:     "summary",
			Short:    "test endpoint",
			Endpoint: "dashboard.summary",
			Method:   "GET",
			Path:     "/api/dashboard/summary",
		},
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("discoverAPIEndpointMethods() = %#v, want %#v", got, want)
	}
}

func TestAPIDiscoverySurfacesEveryCurrentSpecResourceGroup(t *testing.T) {
	var flags rootFlags
	root := newRootCmd(&flags)

	got := interfaceNames(discoverAPIInterfaces(root))
	want := currentSpecResourceGroups(t)
	if len(got) == 0 {
		t.Fatal("api discovery returned no interfaces for the current generated command tree")
	}
	if !reflect.DeepEqual(got, want) {
		t.Fatalf("api interfaces are stale relative to spec.yaml:\n got: %v\nwant: %v", got, want)
	}
}

func TestAPICommandJSONListsOnlyEndpointBackedGroupsWithoutExecutingEndpoints(t *testing.T) {
	var endpointRuns int
	flags := &rootFlags{asJSON: true}
	root := &cobra.Command{Use: "test-cli"}
	resource := &cobra.Command{Use: "resource", Short: "generated resource"}
	endpoint := testEndpointCommand("nested", "resource.nested", "/api/resource/nested")
	endpoint.RunE = func(*cobra.Command, []string) error {
		endpointRuns++
		return nil
	}
	resource.AddCommand(endpoint)
	root.AddCommand(resource)
	root.AddCommand(&cobra.Command{Use: "doctor", Hidden: true})
	root.AddCommand(newAPICmd(flags))

	var output bytes.Buffer
	root.SetOut(&output)
	root.SetErr(&output)
	root.SetArgs([]string{"api"})
	if err := root.Execute(); err != nil {
		t.Fatalf("execute api: %v", err)
	}
	if endpointRuns != 0 {
		t.Fatalf("api discovery executed %d endpoint commands; want pure tree walk", endpointRuns)
	}

	var payload struct {
		Interfaces []struct {
			Name string `json:"name"`
		} `json:"interfaces"`
	}
	if err := json.Unmarshal(output.Bytes(), &payload); err != nil {
		t.Fatalf("decode api JSON: %v\nraw: %s", err, output.String())
	}
	if got, want := len(payload.Interfaces), 1; got != want {
		t.Fatalf("interface count = %d, want %d; payload=%s", got, want, output.String())
	}
	if got, want := payload.Interfaces[0].Name, "resource"; got != want {
		t.Fatalf("interface name = %q, want %q; payload=%s", got, want, output.String())
	}
}

func TestAPICommandInterfaceJSONIncludesEndpointMetadata(t *testing.T) {
	flags := &rootFlags{asJSON: true}
	root := &cobra.Command{Use: "test-cli"}
	resource := &cobra.Command{Use: "resource", Short: "generated resource"}
	nested := &cobra.Command{Use: "nested"}
	nested.AddCommand(testEndpointCommand("get", "resource.nested-get", "/api/resource/{id}"))
	resource.AddCommand(nested)
	root.AddCommand(resource)
	root.AddCommand(newAPICmd(flags))

	var output bytes.Buffer
	root.SetOut(&output)
	root.SetErr(&output)
	root.SetArgs([]string{"api", "resource"})
	if err := root.Execute(); err != nil {
		t.Fatalf("execute api resource: %v", err)
	}

	var payload struct {
		Interface string              `json:"interface"`
		Methods   []apiEndpointMethod `json:"methods"`
	}
	if err := json.Unmarshal(output.Bytes(), &payload); err != nil {
		t.Fatalf("decode api interface JSON: %v\nraw: %s", err, output.String())
	}
	want := []apiEndpointMethod{{
		Name:     "nested get",
		Short:    "test endpoint",
		Endpoint: "resource.nested-get",
		Method:   "GET",
		Path:     "/api/resource/{id}",
	}}
	if payload.Interface != "resource" || !reflect.DeepEqual(payload.Methods, want) {
		t.Fatalf("api interface payload = %#v, want interface resource with methods %#v", payload, want)
	}
}

func testEndpointCommand(name, endpoint, path string) *cobra.Command {
	return &cobra.Command{
		Use:   name,
		Short: "test endpoint",
		Annotations: map[string]string{
			"pp:endpoint": endpoint,
			"pp:method":   "GET",
			"pp:path":     path,
		},
	}
}

func interfaceNames(entries []apiInterfaceEntry) []string {
	names := make([]string, 0, len(entries))
	for _, entry := range entries {
		names = append(names, entry.Name)
	}
	return names
}

// currentSpecResourceGroups reads only the top-level keys directly below the
// internal spec's `resources:` mapping. This keeps the coverage assertion tied
// to the checked-in spec without adding a production YAML dependency or making
// any network request.
func currentSpecResourceGroups(t *testing.T) []string {
	t.Helper()

	f, err := os.Open("../../spec.yaml")
	if err != nil {
		t.Fatalf("open current spec.yaml: %v", err)
	}
	defer f.Close()

	var groups []string
	inResources := false
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := scanner.Text()
		if !inResources {
			if strings.TrimSpace(line) == "resources:" && !strings.HasPrefix(line, " ") {
				inResources = true
			}
			continue
		}
		if line != "" && !strings.HasPrefix(line, " ") && !strings.HasPrefix(line, "#") {
			break
		}
		if !strings.HasPrefix(line, "  ") || strings.HasPrefix(line, "    ") {
			continue
		}
		key := strings.TrimSpace(line)
		if strings.HasSuffix(key, ":") {
			groups = append(groups, strings.TrimSuffix(key, ":"))
		}
	}
	if err := scanner.Err(); err != nil {
		t.Fatalf("scan current spec.yaml: %v", err)
	}
	if len(groups) == 0 {
		t.Fatal("spec.yaml has no resource groups under resources:")
	}
	sort.Strings(groups)
	return groups
}
