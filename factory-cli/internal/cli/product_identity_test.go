// Copyright 2026 daman8271 and contributors. Licensed under Apache-2.0. See LICENSE.

package cli

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

func TestMain(m *testing.M) {
	fixturePath, err := filepath.Abs(filepath.Join("testdata", "product-identity-map.json"))
	if err != nil {
		panic(err)
	}
	fixtureRaw, err := os.ReadFile(fixturePath)
	if err != nil {
		panic(err)
	}
	fixtureSHA := identityPrefixedSHA256(fixtureRaw)
	identityReleaseTrustTestHook = func(mapPath string, mapRaw []byte) (*identityReleaseTrust, bool, error) {
		absolute, pathErr := filepath.Abs(mapPath)
		if pathErr != nil || absolute != fixturePath || identityPrefixedSHA256(mapRaw) != fixtureSHA {
			return nil, false, nil
		}
		return &identityReleaseTrust{
			Path:   "test-only:synthetic-fixture",
			SHA256: fixtureSHA,
		}, true, nil
	}
	code := m.Run()
	identityReleaseTrustTestHook = nil
	os.Exit(code)
}

func fixtureIdentityMapPath(t *testing.T) string {
	t.Helper()
	path, err := filepath.Abs(filepath.Join("testdata", "product-identity-map.json"))
	if err != nil {
		t.Fatal(err)
	}
	return path
}

func runProductCommand(t *testing.T, companyEnv string, args ...string) ([]byte, error) {
	t.Helper()
	oldCompany, hadCompany := os.LookupEnv("JIVO_FACTORY_COMPANY")
	if companyEnv == "" {
		if err := os.Unsetenv("JIVO_FACTORY_COMPANY"); err != nil {
			t.Fatal(err)
		}
	} else if err := os.Setenv("JIVO_FACTORY_COMPANY", companyEnv); err != nil {
		t.Fatal(err)
	}
	defer func() {
		if hadCompany {
			_ = os.Setenv("JIVO_FACTORY_COMPANY", oldCompany)
		} else {
			_ = os.Unsetenv("JIVO_FACTORY_COMPANY")
		}
	}()

	cmd := RootCmd()
	var stdout, stderr bytes.Buffer
	cmd.SetOut(&stdout)
	cmd.SetErr(&stderr)
	cmd.SetArgs(args)
	err := cmd.Execute()
	return stdout.Bytes(), err
}

func decodeIdentityPayload(t *testing.T, raw []byte) map[string]any {
	t.Helper()
	var payload map[string]any
	if err := json.Unmarshal(raw, &payload); err != nil {
		t.Fatalf("invalid JSON output: %v\n%s", err, raw)
	}
	return payload
}

func identityMapMutation(t *testing.T, mutate func(map[string]any)) string {
	t.Helper()
	raw, err := os.ReadFile(fixtureIdentityMapPath(t))
	if err != nil {
		t.Fatal(err)
	}
	var doc map[string]any
	if err := json.Unmarshal(raw, &doc); err != nil {
		t.Fatal(err)
	}
	mutate(doc)
	encoded, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(t.TempDir(), "product-identity-map.json")
	if err := os.WriteFile(path, encoded, 0o600); err != nil {
		t.Fatal(err)
	}
	return path
}

func loadUnattestedIdentityDatasetForTest(t *testing.T, path string) *identityDataset {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	if err := rejectDuplicateIdentityJSONKeys(raw); err != nil {
		t.Fatal(err)
	}
	var doc productIdentityMap
	if err := json.Unmarshal(raw, &doc); err != nil {
		t.Fatal(err)
	}
	if err := validateProductIdentityMap(&doc); err != nil {
		t.Fatalf("synthetic fixture is not structurally valid: %v", err)
	}
	sum := sha256.Sum256(raw)
	return &identityDataset{Map: doc, Path: path, SHA256: hex.EncodeToString(sum[:])}
}

func releasedIdentityV1Path(t *testing.T) string {
	t.Helper()
	path, err := filepath.Abs(filepath.Join("..", "..", "..", "product-identity", "v1"))
	if err != nil {
		t.Fatal(err)
	}
	return path
}

func copyReleasedIdentityBundle(t *testing.T, includeAttestation bool) string {
	t.Helper()
	sourceRoot := releasedIdentityV1Path(t)
	targetRoot := t.TempDir()
	paths := []string{
		"product-identity-map.json",
		"review-decisions.json",
		filepath.Join("sources", "ecom-master-products.json"),
		filepath.Join("sources", "factory-catalogs.json"),
		filepath.Join("sources", "jid-registry.json"),
		filepath.Join("sources", "pricematch-master-v2.json"),
		filepath.Join("sources", "pricematch-sku-map.json"),
	}
	if includeAttestation {
		paths = append(paths, identityAttestationFilename)
	}
	for _, relative := range paths {
		raw, err := os.ReadFile(filepath.Join(sourceRoot, relative))
		if err != nil {
			t.Fatal(err)
		}
		target := filepath.Join(targetRoot, relative)
		if err := os.MkdirAll(filepath.Dir(target), 0o700); err != nil {
			t.Fatal(err)
		}
		if err := os.WriteFile(target, raw, 0o600); err != nil {
			t.Fatal(err)
		}
	}
	return filepath.Join(targetRoot, "product-identity-map.json")
}

func mutateIdentityJSONFile(t *testing.T, path string, mutate func(map[string]any)) {
	t.Helper()
	raw, err := os.ReadFile(path)
	if err != nil {
		t.Fatal(err)
	}
	var doc map[string]any
	if err := json.Unmarshal(raw, &doc); err != nil {
		t.Fatal(err)
	}
	mutate(doc)
	encoded, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		t.Fatal(err)
	}
	encoded = append(encoded, '\n')
	if err := os.WriteFile(path, encoded, 0o600); err != nil {
		t.Fatal(err)
	}
}

func rebuildFactoryAccountingForTest(t *testing.T, doc map[string]any) {
	t.Helper()
	used := map[string]map[string]struct{}{}
	for _, rawResolution := range doc["resolutions"].([]any) {
		resolution := rawResolution.(map[string]any)
		listingKey := resolution["listing_key"].(string)
		for _, rawBinding := range resolution["factory_bindings"].([]any) {
			binding := rawBinding.(map[string]any)
			factoryKey := binding["factory_item_key"].(string)
			if used[factoryKey] == nil {
				used[factoryKey] = map[string]struct{}{}
			}
			used[factoryKey][listingKey] = struct{}{}
		}
	}
	for _, rawAccounting := range doc["factory_item_accounting"].([]any) {
		accounting := rawAccounting.(map[string]any)
		factoryKey := accounting["factory_item_key"].(string)
		listings := make([]string, 0, len(used[factoryKey]))
		for listingKey := range used[factoryKey] {
			listings = append(listings, listingKey)
		}
		sort.Strings(listings)
		encodedListings := make([]any, len(listings))
		for index, listingKey := range listings {
			encodedListings[index] = listingKey
		}
		accounting["listing_keys"] = encodedListings
		if len(listings) > 0 {
			accounting["disposition"] = "mapped"
			accounting["reason"] = "Test recomputation: at least one exact listing binds this qualified item."
		} else {
			accounting["disposition"] = "not_in_price_scraping_scope"
			accounting["reason"] = "Test recomputation: no exact current listing binds this qualified item."
		}
	}
}

func TestProductVerifyReleasedMapIncludesVersionAndHash(t *testing.T) {
	out, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "verify")
	if err != nil {
		t.Fatalf("verify failed: %v", err)
	}
	payload := decodeIdentityPayload(t, out)
	if payload["valid"] != true || payload["map_version"] != "fixture-2026-07-19" || payload["schema_version"] != "1.0.0" {
		t.Fatalf("unexpected verify payload: %#v", payload)
	}
	hash, _ := payload["map_sha256"].(string)
	if len(hash) != 64 {
		t.Fatalf("map_sha256 length=%d, want 64 (%q)", len(hash), hash)
	}
}

func TestProductIdentityMapCanComeFromEnvironment(t *testing.T) {
	t.Setenv("JIVO_PRODUCT_IDENTITY_MAP", fixtureIdentityMapPath(t))
	out, err := runProductCommand(t, "", "product", "verify")
	if err != nil {
		t.Fatalf("verify through JIVO_PRODUCT_IDENTITY_MAP failed: %v", err)
	}
	if decodeIdentityPayload(t, out)["valid"] != true {
		t.Fatalf("environment-selected map did not verify: %s", out)
	}
}

func TestProductResolveBareFactoryCodeNeverDefaultsMart(t *testing.T) {
	_, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "resolve", "FG0000391")
	if err == nil {
		t.Fatal("bare Factory code unexpectedly resolved without company")
	}
	if got := ExitCode(err); got != 2 {
		t.Fatalf("ExitCode=%d, want 2: %v", got, err)
	}
	if !strings.Contains(err.Error(), "requires --company") || !strings.Contains(err.Error(), "never assumed") {
		t.Fatalf("error does not explain safe qualification: %v", err)
	}
}

func TestProductResolveBareFactoryCodeUsesExplicitCompany(t *testing.T) {
	out, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "resolve", "FG0000391", "--company", "mart")
	if err != nil {
		t.Fatalf("resolve failed: %v", err)
	}
	payload := decodeIdentityPayload(t, out)
	matches := payload["matches"].([]any)
	if len(matches) != 1 {
		t.Fatalf("matches=%d, want 1: %#v", len(matches), matches)
	}
	match := matches[0].(map[string]any)
	if match["company_code"] != "JIVO_MART" || match["sap_schema"] != "JIVO_MART_HANADB" || match["factory_item_key"] != "urn:jivo:factory:JIVO_MART:JIVO_MART_HANADB:FG0000391" {
		t.Fatalf("wrong qualified Mart identity: %#v", match)
	}
	if !strings.Contains(match["factory_item_name"].(string), "EXTRA VIRGIN") {
		t.Fatalf("Mart collision resolved to wrong product: %#v", match)
	}
}

func TestProductResolveAllCompaniesReturnsQualifiedCollision(t *testing.T) {
	out, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "resolve", "FG0000391", "--all-companies")
	if err != nil {
		t.Fatalf("resolve --all-companies failed: %v", err)
	}
	payload := decodeIdentityPayload(t, out)
	matches := payload["matches"].([]any)
	if len(matches) != 2 {
		t.Fatalf("matches=%d, want 2: %#v", len(matches), matches)
	}
	companies := map[string]bool{}
	for _, raw := range matches {
		match := raw.(map[string]any)
		companies[match["company_code"].(string)] = true
		if match["sap_schema"] == "" || match["factory_item_key"] == "" {
			t.Fatalf("collision row is not qualified: %#v", match)
		}
	}
	if !companies["JIVO_MART"] || !companies["JIVO_OIL"] {
		t.Fatalf("qualified companies=%v, want Mart and Oil", companies)
	}
}

func TestProductResolveExactNamespacesAndNoTextFallback(t *testing.T) {
	for _, identifier := range []string{
		"JID-0143",
		"urn:jivo:product:JID-0143",
		"urn:jivo:price-sku:price-match:EXTRA%20VIRGIN%203L",
		"EXTRA VIRGIN 3L",
		"price-match:EXTRA VIRGIN 3L",
		"urn:jivo:listing:amazon:B0EXTRA3L",
		"amazon:B0EXTRA3L",
		"B0EXTRA3L",
		"urn:jivo:factory:JIVO_MART:JIVO_MART_HANADB:FG0000391",
		"JIVO_MART:JIVO_MART_HANADB:FG0000391",
	} {
		out, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "resolve", identifier)
		if err != nil {
			t.Fatalf("resolve %q failed: %v", identifier, err)
		}
		payload := decodeIdentityPayload(t, out)
		if len(payload["matches"].([]any)) == 0 {
			t.Fatalf("resolve %q returned no matches", identifier)
		}
	}
	_, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "resolve", "Extra Virgin Olive Oil")
	if err == nil || ExitCode(err) != 3 {
		t.Fatalf("name unexpectedly used as an identity join: %v", err)
	}
	out, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "search", "Extra Virgin Olive Oil")
	if err != nil {
		t.Fatalf("text search failed: %v", err)
	}
	if len(decodeIdentityPayload(t, out)["matches"].([]any)) == 0 {
		t.Fatal("text search returned no results")
	}
}

func TestProductResolveAliasJIDReachesCanonicalBindings(t *testing.T) {
	out, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "resolve", "JID-0142")
	if err != nil {
		t.Fatalf("resolve alias JID failed: %v", err)
	}
	payload := decodeIdentityPayload(t, out)
	if payload["identifier_kind"] != "jid_alias" {
		t.Fatalf("identifier_kind=%v, want jid_alias", payload["identifier_kind"])
	}
	match := payload["matches"].([]any)[0].(map[string]any)
	if match["jid"] != "JID-0143" || match["factory_item_key"] != "urn:jivo:factory:JIVO_MART:JIVO_MART_HANADB:FG0000391" {
		t.Fatalf("alias did not resolve through canonical bindings: %#v", match)
	}
}

func TestProductCatalogRequiresAndReportsExplicitCompany(t *testing.T) {
	_, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "catalog")
	if err == nil || ExitCode(err) != 2 {
		t.Fatalf("catalog without company should exit 2, got: %v", err)
	}
	out, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "catalog", "--company", "oil")
	if err != nil {
		t.Fatalf("catalog failed: %v", err)
	}
	payload := decodeIdentityPayload(t, out)
	if payload["company_code"] != "JIVO_OIL" || payload["count"] != float64(1) {
		t.Fatalf("unexpected catalog payload: %#v", payload)
	}
	item := payload["items"].([]any)[0].(map[string]any)
	if item["sap_schema"] != "JIVO_OIL_HANADB" || item["factory_item_key"] == "" || item["disposition"] != "mapped" {
		t.Fatalf("catalog item is not fully qualified: %#v", item)
	}
}

func TestProductMapFailuresUseExitCode6(t *testing.T) {
	cases := map[string]func(map[string]any){
		"draft": func(doc map[string]any) {
			doc["contract"].(map[string]any)["release_status"] = "draft"
		},
		"unsupported major": func(doc map[string]any) {
			doc["contract"].(map[string]any)["schema_version"] = "2.0.0"
		},
		"incomplete": func(doc map[string]any) {
			doc["resolutions"] = []any{}
		},
		"missing factory accounting row": func(doc map[string]any) {
			doc["factory_item_accounting"] = doc["factory_item_accounting"].([]any)[:1]
		},
		"unaccounted bare-code collision": func(doc map[string]any) {
			doc["factory_code_collisions"] = []any{}
		},
		"binding lacks two-sided evidence": func(doc map[string]any) {
			binding := doc["resolutions"].([]any)[0].(map[string]any)["factory_bindings"].([]any)[0].(map[string]any)
			binding["evidence"] = binding["evidence"].([]any)[:1]
		},
		"evidence references unknown source": func(doc map[string]any) {
			evidence := doc["listings"].([]any)[0].(map[string]any)["evidence"].([]any)[0].(map[string]any)
			evidence["source_id"] = "missing-source"
		},
		"unmapped disposition contradicts binding": func(doc map[string]any) {
			accounting := doc["factory_item_accounting"].([]any)[0].(map[string]any)
			accounting["disposition"] = "not_in_price_scraping_scope"
			accounting["listing_keys"] = []any{}
			accounting["reason"] = "Incorrectly claims this bound item is out of scope."
		},
		"incomplete source mapping coverage": func(doc map[string]any) {
			coverage := doc["coverage"].(map[string]any)["source_mapping_rows"].(map[string]any)
			coverage["accounted"] = float64(1)
			coverage["unaccounted"] = float64(1)
		},
		"source is not read only": func(doc map[string]any) {
			doc["sources"].([]any)[0].(map[string]any)["read_only"] = false
		},
		"derived listing key disagrees": func(doc map[string]any) {
			doc["listings"].([]any)[0].(map[string]any)["platform"] = "tampered-platform"
		},
		"unknown Factory binding role": func(doc map[string]any) {
			binding := doc["resolutions"].([]any)[0].(map[string]any)["factory_bindings"].([]any)[0].(map[string]any)
			binding["role"] = "mystery-role"
		},
		"missing listing pack": func(doc map[string]any) {
			delete(doc["listings"].([]any)[0].(map[string]any), "pack")
		},
		"missing resolution evidence": func(doc map[string]any) {
			delete(doc["resolutions"].([]any)[0].(map[string]any), "evidence")
		},
		"missing product evidence": func(doc map[string]any) {
			delete(doc["products"].([]any)[0].(map[string]any), "evidence")
		},
		"resolution targets alias JID": func(doc map[string]any) {
			resolution := doc["resolutions"].([]any)[0].(map[string]any)
			resolution["canonical_product_key"] = "urn:jivo:product:JID-0142"
			resolution["canonical_jid"] = "JID-0142"
		},
		"unknown alias relation": func(doc map[string]any) {
			doc["jid_aliases"].([]any)[0].(map[string]any)["relation"] = "mystery-relation"
		},
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			path := identityMapMutation(t, mutate)
			_, err := runProductCommand(t, "", "product", "--identity-map", path, "verify")
			if err == nil {
				t.Fatal("invalid map unexpectedly verified")
			}
			if got := ExitCode(err); got != 6 {
				t.Fatalf("ExitCode=%d, want 6: %v", got, err)
			}
		})
	}
}

func TestProductReleaseAttestationRejectsSemanticallyConsistentTampering(t *testing.T) {
	cases := map[string]func(*testing.T, map[string]any){
		"source hash drift": func(t *testing.T, doc map[string]any) {
			doc["sources"].([]any)[0].(map[string]any)["content_sha256"] = "sha256:" + strings.Repeat("0", 64)
		},
		"Shikanji cross-company rewrite": func(t *testing.T, doc map[string]any) {
			const listingKey = "urn:jivo:listing:amazon:B0GZ7PXVF8"
			const oldFactory = "urn:jivo:factory:JIVO_BEVERAGES:JIVO_BEVERAGES_HANADB:FG0000315"
			const wrongFactory = "urn:jivo:factory:JIVO_MART:JIVO_MART_HANADB:FG0000315"
			found := false
			for _, rawResolution := range doc["resolutions"].([]any) {
				resolution := rawResolution.(map[string]any)
				if resolution["listing_key"] != listingKey {
					continue
				}
				for _, rawBinding := range resolution["factory_bindings"].([]any) {
					binding := rawBinding.(map[string]any)
					if binding["factory_item_key"] != oldFactory {
						continue
					}
					binding["factory_item_key"] = wrongFactory
					found = true
				}
			}
			if !found {
				t.Fatal("released map lacks expected Shikanji binding")
			}
			rebuildFactoryAccountingForTest(t, doc)
		},
		"Sano Extra collapsed into Classic": func(t *testing.T, doc map[string]any) {
			const listingKey = "urn:jivo:listing:amazon:B0CCVF1XVS"
			found := false
			for _, rawResolution := range doc["resolutions"].([]any) {
				resolution := rawResolution.(map[string]any)
				if resolution["listing_key"] != listingKey {
					continue
				}
				resolution["canonical_product_key"] = "urn:jivo:product:JID-0051"
				resolution["canonical_jid"] = "JID-0051"
				found = true
			}
			if !found {
				t.Fatal("released map lacks expected Sano Extra listing")
			}
		},
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			path := copyReleasedIdentityBundle(t, true)
			mutateIdentityJSONFile(t, path, func(doc map[string]any) { mutate(t, doc) })
			// Prove this attack survives the consumer's ordinary structural
			// checks. The detached trust anchor—not a coincidental shape error—
			// must be what prevents operational use.
			_ = loadUnattestedIdentityDatasetForTest(t, path)
			_, err := runProductCommand(t, "", "product", "--identity-map", path, "verify")
			if err == nil || ExitCode(err) != 6 {
				t.Fatalf("semantically tampered release should exit 6, got: %v", err)
			}
			if !strings.Contains(err.Error(), "attest") && !strings.Contains(err.Error(), "digest") {
				t.Fatalf("tamper rejection did not identify release trust: %v", err)
			}
		})
	}
}

func TestProductReleaseAttestationRejectsBundleTampering(t *testing.T) {
	t.Run("missing attestation", func(t *testing.T) {
		path := copyReleasedIdentityBundle(t, false)
		_, err := runProductCommand(t, "", "product", "--identity-map", path, "verify")
		if err == nil || ExitCode(err) != 6 {
			t.Fatalf("missing attestation should exit 6, got: %v", err)
		}
	})

	t.Run("edited attestation", func(t *testing.T) {
		path := copyReleasedIdentityBundle(t, true)
		attestationPath := filepath.Join(filepath.Dir(path), identityAttestationFilename)
		raw, err := os.ReadFile(attestationPath)
		if err != nil {
			t.Fatal(err)
		}
		raw = append(raw, '\n')
		if err := os.WriteFile(attestationPath, raw, 0o600); err != nil {
			t.Fatal(err)
		}
		_, err = runProductCommand(t, "", "product", "--identity-map", path, "verify")
		if err == nil || ExitCode(err) != 6 {
			t.Fatalf("edited attestation should exit 6, got: %v", err)
		}
	})

	t.Run("edited evidence snapshot", func(t *testing.T) {
		path := copyReleasedIdentityBundle(t, true)
		evidencePath := filepath.Join(filepath.Dir(path), "sources", "jid-registry.json")
		raw, err := os.ReadFile(evidencePath)
		if err != nil {
			t.Fatal(err)
		}
		raw = append(raw, '\n')
		if err := os.WriteFile(evidencePath, raw, 0o600); err != nil {
			t.Fatal(err)
		}
		_, err = runProductCommand(t, "", "product", "--identity-map", path, "verify")
		if err == nil || ExitCode(err) != 6 {
			t.Fatalf("edited evidence should exit 6, got: %v", err)
		}
	})

	t.Run("alternate map without release bundle", func(t *testing.T) {
		source := filepath.Join(releasedIdentityV1Path(t), "product-identity-map.json")
		raw, err := os.ReadFile(source)
		if err != nil {
			t.Fatal(err)
		}
		path := filepath.Join(t.TempDir(), "product-identity-map.json")
		if err := os.WriteFile(path, raw, 0o600); err != nil {
			t.Fatal(err)
		}
		_, err = runProductCommand(t, "", "product", "--identity-map", path, "verify")
		if err == nil || ExitCode(err) != 6 {
			t.Fatalf("alternate unbundled map should exit 6, got: %v", err)
		}
	})
}

func TestProductMapRejectsDuplicateJSONKeys(t *testing.T) {
	raw, err := os.ReadFile(fixtureIdentityMapPath(t))
	if err != nil {
		t.Fatal(err)
	}
	needle := []byte(`"release_status": "released",`)
	replacement := []byte(`"release_status": "draft", "release_status": "released",`)
	malformed := bytes.Replace(raw, needle, replacement, 1)
	if bytes.Equal(raw, malformed) {
		t.Fatal("fixture replacement did not add duplicate key")
	}
	path := filepath.Join(t.TempDir(), "duplicate-key-map.json")
	if err := os.WriteFile(path, malformed, 0o600); err != nil {
		t.Fatal(err)
	}
	_, err = runProductCommand(t, "", "product", "--identity-map", path, "verify")
	if err == nil || ExitCode(err) != 6 || !strings.Contains(err.Error(), "duplicate object key") {
		t.Fatalf("duplicate JSON key should exit 6, got: %v", err)
	}
}

func TestProductMapSupportsNullableJIDAndReviewedAbsentContract(t *testing.T) {
	path := identityMapMutation(t, func(doc map[string]any) {
		products := doc["products"].([]any)
		product := products[1].(map[string]any)
		product["jid"] = nil
		product["product_key"] = "urn:jivo:product:local:sesame-jeera-combo"
		jidCoverage := doc["coverage"].(map[string]any)["jids"].(map[string]any)
		jidCoverage["expected"] = float64(2)
		jidCoverage["accounted"] = float64(2)
		resolutions := doc["resolutions"].([]any)
		resolution := resolutions[1].(map[string]any)
		resolution["canonical_jid"] = nil
		resolution["canonical_product_key"] = "urn:jivo:product:local:sesame-jeera-combo"
		resolution["factory_mapping_state"] = "reviewed_absent"
		resolution["factory_bindings"] = []any{}
		resolution["factory_absence"] = map[string]any{
			"reason_code": "not_present_in_complete_factory_catalog",
			"reason":      "No qualified item exists in the complete fixture catalogs.",
			"scopes_checked": []any{
				"urn:jivo:factory-scope:JIVO_MART:JIVO_MART_HANADB",
				"urn:jivo:factory-scope:JIVO_OIL:JIVO_OIL_HANADB",
				"urn:jivo:factory-scope:JIVO_BEVERAGES:JIVO_BEVERAGES_HANADB",
			},
			"evidence": []any{
				map[string]any{"source_id": "fixture", "pointer": "/listings/0", "claim": "Exact marketplace listing.", "evidence_kind": "exact_listing_identity"},
				map[string]any{"source_id": "fixture", "pointer": "/factory_scopes", "claim": "Complete catalog search found no matching qualified item.", "evidence_kind": "complete_catalog_absence"},
			},
		}
		accounting := doc["factory_item_accounting"].([]any)[1].(map[string]any)
		accounting["disposition"] = "not_in_price_scraping_scope"
		accounting["listing_keys"] = []any{}
		accounting["reason"] = "Fixture switches this listing to reviewed absence."
	})
	dataset := loadUnattestedIdentityDatasetForTest(t, path)
	_, matches, err := dataset.resolveExact(
		"urn:jivo:product:local:sesame-jeera-combo",
		&rootFlags{companyCode: "JIVO_BEVERAGES", companyExplicit: true},
		false,
	)
	if err != nil {
		t.Fatalf("nullable-JID reviewed-absent map failed: %v", err)
	}
	if len(matches) != 1 {
		t.Fatalf("nullable-JID resolution returned %d matches, want 1", len(matches))
	}
	match := matches[0]
	if match.ProductKey != "urn:jivo:product:local:sesame-jeera-combo" {
		t.Fatalf("wrong nullable-JID product result: %#v", match)
	}
	if match.JID != "" {
		t.Fatalf("nullable JID should stay empty, got: %#v", match)
	}
	if match.FactoryMappingState != "reviewed_absent" || match.FactoryAbsence == nil {
		t.Fatalf("reviewed absence was not preserved under --company: %#v", match)
	}
}

func TestProductMapRejectsUnprovedReviewedAbsence(t *testing.T) {
	path := identityMapMutation(t, func(doc map[string]any) {
		resolution := doc["resolutions"].([]any)[0].(map[string]any)
		resolution["factory_mapping_state"] = "reviewed_absent"
		resolution["factory_bindings"] = []any{}
		resolution["factory_absence"] = map[string]any{
			"reason_code":    "source_gap",
			"reason":         "Unproven gap",
			"scopes_checked": []any{"urn:jivo:factory-scope:JIVO_MART:JIVO_MART_HANADB"},
			"evidence":       []any{},
		}
	})
	_, err := runProductCommand(t, "", "product", "--identity-map", path, "verify")
	if err == nil || ExitCode(err) != 6 {
		t.Fatalf("unproved reviewed absence should exit 6, got: %v", err)
	}
}

func TestProductMapAllowsExplicitEquivalentWithoutPrimary(t *testing.T) {
	path := identityMapMutation(t, func(doc map[string]any) {
		binding := doc["resolutions"].([]any)[0].(map[string]any)["factory_bindings"].([]any)[0].(map[string]any)
		binding["primary_for_scope"] = false
	})
	_ = loadUnattestedIdentityDatasetForTest(t, path)
}

func TestProductResolvePreservesExplicitNullUnprovenConversion(t *testing.T) {
	path := identityMapMutation(t, func(doc map[string]any) {
		binding := doc["resolutions"].([]any)[0].(map[string]any)["factory_bindings"].([]any)[0].(map[string]any)
		binding["conversion_state"] = "not_proven"
		binding["factory_uom_per_listing_offer"] = nil
	})
	dataset := loadUnattestedIdentityDatasetForTest(t, path)
	_, matches, err := dataset.resolveExact("B0EXTRA3L", &rootFlags{}, false)
	if err != nil {
		t.Fatalf("resolve failed: %v", err)
	}
	if len(matches) == 0 {
		t.Fatal("resolve returned no matches")
	}
	match := matches[0]
	if match.FactoryUOMPerListingOffer == nil || *match.FactoryUOMPerListingOffer != nil || match.ConversionState != "not_proven" {
		t.Fatalf("unproved conversion must be explicit null, got: %#v", match)
	}
}

func TestProductCommandsContainNoRemoteMutationSurface(t *testing.T) {
	raw, err := os.ReadFile("product_identity.go")
	if err != nil {
		t.Fatal(err)
	}
	upper := strings.ToUpper(string(raw))
	for _, method := range []string{"HTTP.POST", "HTTP.PUT", "HTTP.PATCH", "HTTP.DELETE", "NEWREQUEST(\"POST\"", "NEWREQUEST(\"PUT\"", "NEWREQUEST(\"PATCH\"", "NEWREQUEST(\"DELETE\""} {
		if strings.Contains(upper, method) {
			t.Fatalf("product identity consumer contains remote mutation surface %q", method)
		}
	}
}

func TestProductCommandsAreDiscoverableThroughWhich(t *testing.T) {
	matches := rankWhich(whichIndex, "product identity mapping", 10)
	commands := map[string]bool{}
	for _, match := range matches {
		commands[match.Entry.Command] = true
	}
	for _, command := range []string{"product resolve", "product verify", "product coverage"} {
		if !commands[command] {
			t.Fatalf("which index did not discover %q: %+v", command, matches)
		}
	}
}

func TestProductResolveExposesSelectionSafetyMetadata(t *testing.T) {
	out, err := runProductCommand(t, "", "product", "--identity-map", fixtureIdentityMapPath(t), "resolve", "B0EXTRA3L")
	if err != nil {
		t.Fatalf("resolve failed: %v", err)
	}
	match := decodeIdentityPayload(t, out)["matches"].([]any)[0].(map[string]any)
	if match["primary_for_scope"] != true || match["factory_accounting_disposition"] != "mapped" || match["factory_collision_relation"] != "different_offer" {
		t.Fatalf("selection safety metadata is incomplete: %#v", match)
	}
	if match["listing_pack"] == nil || match["verification_method"] == "" || match["resolution_evidence"] == nil || match["factory_binding_evidence"] == nil {
		t.Fatalf("pack/provenance metadata is incomplete: %#v", match)
	}
}

func TestProductIdentityRealReleasedMapIntegration(t *testing.T) {
	path, err := filepath.Abs(filepath.Join("..", "..", "..", "product-identity", "v1", "product-identity-map.json"))
	if err != nil {
		t.Fatal(err)
	}
	if _, err := os.Stat(path); os.IsNotExist(err) {
		t.Skip("shared product identity artifact is not present in this checkout")
	} else if err != nil {
		t.Fatal(err)
	}
	dataset, err := loadIdentityDataset(path)
	if err != nil {
		t.Fatalf("released shared map failed Factory consumer verification: %v", err)
	}
	if dataset.AttestationSHA256 != identityTrustedAttestationSHA256 || filepath.Base(dataset.AttestationPath) != identityAttestationFilename {
		t.Fatalf("released map did not retain trusted detached attestation metadata: %+v", dataset)
	}
	if dataset.Map.Contract.DatasetVersion == "2026-07-19.1" && dataset.SHA256 != "ec0998527760a9e47450d0a7c81d1216b299ecaade069a08c6b02c932de7a5b9" {
		t.Fatalf("unexpected hash for released map 2026-07-19.1: %s", dataset.SHA256)
	}

	kind, rows, err := dataset.resolveExact("EDOFRXTMJGAE9DCT", &rootFlags{}, false)
	if err != nil {
		t.Fatalf("double-membership listing failed to resolve: %v", err)
	}
	if kind != "listing_id" {
		t.Fatalf("identifier kind=%q, want listing_id", kind)
	}
	priceCodes := map[string]bool{}
	for _, row := range rows {
		priceCodes[row.SourceProductCode] = true
		if row.ConversionState != "not_proven" || row.FactoryUOMPerListingOffer == nil || *row.FactoryUOMPerListingOffer != nil {
			t.Fatalf("released nullable conversion was altered or invented: %+v", row)
		}
	}
	if !priceCodes["CANOLA 1+1L"] || !priceCodes["CANOLA 1L + 1L"] {
		t.Fatalf("double source membership was flattened: %v", priceCodes)
	}

	for _, itemCode := range []string{"FG0000315", "FG0000391"} {
		_, collisionRows, err := dataset.resolveExact(itemCode, &rootFlags{}, true)
		if err != nil {
			t.Fatalf("hazard code %s failed to resolve across companies: %v", itemCode, err)
		}
		companies := map[string]bool{}
		names := map[string]bool{}
		for _, row := range collisionRows {
			if row.CompanyCode == "" || row.SAPSchema == "" || row.FactoryItemKey == "" || row.FactoryCollisionRelation == "" {
				t.Fatalf("hazard code %s returned an unqualified collision row: %+v", itemCode, row)
			}
			companies[row.CompanyCode] = true
			names[row.FactoryItemName] = true
		}
		if len(companies) < 2 || len(names) < 2 {
			t.Fatalf("hazard code %s was silently conflated: companies=%v names=%v", itemCode, companies, names)
		}
	}
}
