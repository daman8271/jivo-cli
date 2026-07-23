// Copyright 2026 daman8271 and contributors. Licensed under Apache-2.0. See LICENSE.
// Hand-authored: read-only consumer for JivoGPT's shared product identity map.

package cli

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/url"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

const (
	identityContractName             = "jivo-product-identity"
	identityAttestationContractName  = "jivo-product-identity-release-attestation"
	identitySupportedMajor           = 1
	identityDefaultRelativeMap       = "CLI/product-identity/v1/product-identity-map.json"
	identityAttestationFilename      = "release-attestation.json"
	identityAttestationFormatVersion = "1.0.0"
	// Updated only after the independent verifier approves a complete release.
	// The detached attestation then anchors both the map bytes and every frozen
	// evidence artifact. A map cannot approve its own replacement.
	identityTrustedAttestationSHA256 = "sha256:ae8d1ad9892d20f6d2e5f36eba3c54488f78788b6f4fab496c9d7b296e49b6ac"
)

// identityMapErr is intentionally exit code 6. A product identity command
// must fail closed when its local contract is absent, draft, unsupported, or
// incomplete; falling back to a guessed Factory item would be data corruption.
func identityMapErr(err error) error { return &cliError{code: 6, err: err} }

type identityContract struct {
	Name             string `json:"name"`
	SchemaVersion    string `json:"schema_version"`
	DatasetVersion   string `json:"dataset_version"`
	ReleaseStatus    string `json:"release_status"`
	GeneratedAt      string `json:"generated_at"`
	GeneratorVersion string `json:"generator_version"`
	ReadOnly         *bool  `json:"read_only"`
}

type identitySource struct {
	SourceID           string `json:"source_id"`
	Kind               string `json:"kind"`
	URI                string `json:"uri"`
	ObservedAt         string `json:"observed_at"`
	ContentSHA256      string `json:"content_sha256"`
	IdentitySetSHA256  string `json:"identity_set_sha256"`
	RecordCount        *int   `json:"record_count"`
	PaginationComplete *bool  `json:"pagination_complete"`
	ReadOnly           *bool  `json:"read_only"`
}

type identityAttestationMap struct {
	URI    string `json:"uri"`
	SHA256 string `json:"sha256"`
}

type identityAttestationArtifact struct {
	SourceID string `json:"source_id"`
	URI      string `json:"uri"`
	SHA256   string `json:"sha256"`
}

type identityAttestationVerification struct {
	VerifierVersion string `json:"verifier_version"`
	CheckCount      int    `json:"check_count"`
}

type identityReleaseAttestation struct {
	FormatVersion     string                          `json:"format_version"`
	ContractName      string                          `json:"contract_name"`
	DatasetVersion    string                          `json:"dataset_version"`
	SchemaVersion     string                          `json:"schema_version"`
	ReleaseStatus     string                          `json:"release_status"`
	Map               identityAttestationMap          `json:"map"`
	EvidenceArtifacts []identityAttestationArtifact   `json:"evidence_artifacts"`
	Verification      identityAttestationVerification `json:"verification"`
}

type identityReleaseTrust struct {
	Path   string
	SHA256 string
}

type identityProduct struct {
	ProductKey    string          `json:"product_key"`
	JID           string          `json:"jid"`
	CanonicalName string          `json:"canonical_name"`
	State         string          `json:"state"`
	Evidence      json.RawMessage `json:"evidence,omitempty"`
}

type identityPriceSKU struct {
	PriceSKUKey       string          `json:"price_sku_key"`
	SourceNamespace   string          `json:"source_namespace"`
	SourceProductCode string          `json:"source_product_code"`
	DisplayName       string          `json:"display_name"`
	State             string          `json:"state"`
	MemberListingKeys []string        `json:"member_listing_keys"`
	Evidence          json.RawMessage `json:"evidence,omitempty"`
}

type identityListing struct {
	ListingKey        string                     `json:"listing_key"`
	PriceSKUKey       string                     `json:"price_sku_key"`
	PriceSKUKeys      []string                   `json:"price_sku_keys"`
	SourceMemberships []identitySourceMembership `json:"source_memberships"`
	Platform          string                     `json:"platform"`
	ListingID         string                     `json:"listing_id"`
	ListingIDKind     string                     `json:"listing_id_kind"`
	Title             string                     `json:"title"`
	State             string                     `json:"state"`
	IsPrimary         *bool                      `json:"is_primary"`
	Pack              json.RawMessage            `json:"pack,omitempty"`
	Evidence          json.RawMessage            `json:"evidence,omitempty"`
}

type identitySourceMembership struct {
	PriceSKUKey string `json:"price_sku_key"`
	Role        string `json:"role"`
}

type identityPack struct {
	Kind            string            `json:"kind"`
	Components      []json.RawMessage `json:"components"`
	PackFingerprint string            `json:"pack_fingerprint"`
}

type identityFactoryItem struct {
	FactoryItemKey  string          `json:"factory_item_key"`
	FactoryScopeKey string          `json:"factory_scope_key"`
	CompanyCode     string          `json:"company_code"`
	SAPSchema       string          `json:"sap_schema"`
	ItemCode        string          `json:"item_code"`
	ItemName        string          `json:"item_name"`
	ItemClass       string          `json:"item_class"`
	State           string          `json:"state"`
	Evidence        json.RawMessage `json:"evidence,omitempty"`
}

type identityFactoryScope struct {
	FactoryScopeKey string `json:"factory_scope_key"`
	CompanyCode     string `json:"company_code"`
	CompanyID       *int   `json:"company_id"`
	SAPSchema       string `json:"sap_schema"`
}

type identityRatio struct {
	Numerator   int `json:"numerator"`
	Denominator int `json:"denominator"`
}

type identityFactoryBinding struct {
	FactoryItemKey            string          `json:"factory_item_key"`
	Role                      string          `json:"role"`
	FactoryUOMPerListingOffer *identityRatio  `json:"factory_uom_per_listing_offer"`
	ConversionState           string          `json:"conversion_state"`
	PrimaryForScope           *bool           `json:"primary_for_scope"`
	Evidence                  json.RawMessage `json:"evidence,omitempty"`
}

type identityResolution struct {
	ResolutionID        string                   `json:"resolution_id"`
	ListingKey          string                   `json:"listing_key"`
	CanonicalProductKey string                   `json:"canonical_product_key"`
	CanonicalJID        string                   `json:"canonical_jid"`
	State               string                   `json:"state"`
	FactoryMappingState string                   `json:"factory_mapping_state"`
	FactoryBindings     []identityFactoryBinding `json:"factory_bindings"`
	FactoryAbsence      *identityFactoryAbsence  `json:"factory_absence,omitempty"`
	VerificationMethod  string                   `json:"verification_method"`
	VerifiedBy          string                   `json:"verified_by"`
	VerifiedAt          string                   `json:"verified_at"`
	Evidence            json.RawMessage          `json:"evidence,omitempty"`
}

type identityFactoryAbsence struct {
	ReasonCode    string            `json:"reason_code"`
	Reason        string            `json:"reason"`
	ScopesChecked []string          `json:"scopes_checked"`
	Evidence      []json.RawMessage `json:"evidence"`
}

type identityCoverageCounter struct {
	Expected    int `json:"expected"`
	Accounted   int `json:"accounted"`
	Unaccounted int `json:"unaccounted"`
}

type identityCoverage struct {
	PriceSKUs                 *identityCoverageCounter `json:"price_skus"`
	ActivePriceSKUs           *identityCoverageCounter `json:"active_price_skus"`
	SourceMappingRows         *identityCoverageCounter `json:"source_mapping_rows"`
	Listings                  *identityCoverageCounter `json:"listings"`
	JIDs                      *identityCoverageCounter `json:"jids"`
	FactoryItems              *identityCoverageCounter `json:"factory_items"`
	UnresolvedListings        json.RawMessage          `json:"unresolved_listings"`
	UnresolvedActiveListings  json.RawMessage          `json:"unresolved_active_listings"`
	AmbiguousListings         json.RawMessage          `json:"ambiguous_listings"`
	OpenJIDConflicts          json.RawMessage          `json:"open_jid_conflicts"`
	UnknownFactoryCollisions  json.RawMessage          `json:"unknown_factory_collisions"`
	SourceIdentitySetsMatch   *bool                    `json:"source_identity_sets_match"`
	QueueEntriesOutsideMaster json.RawMessage          `json:"queue_entries_outside_current_master"`
}

type productIdentityMap struct {
	Contract                identityContract      `json:"contract"`
	Sources                 []json.RawMessage     `json:"sources"`
	FactoryScopes           []json.RawMessage     `json:"factory_scopes"`
	Products                []identityProduct     `json:"products"`
	PriceSKUs               []identityPriceSKU    `json:"price_skus"`
	Listings                []identityListing     `json:"listings"`
	FactoryItems            []identityFactoryItem `json:"factory_items"`
	Resolutions             []identityResolution  `json:"resolutions"`
	JIDAliases              []json.RawMessage     `json:"jid_aliases"`
	JIDConflicts            []json.RawMessage     `json:"jid_conflicts"`
	FactoryItemAccounting   []json.RawMessage     `json:"factory_item_accounting"`
	FactoryCodeCollisions   []json.RawMessage     `json:"factory_code_collisions"`
	ObservedQueueAccounting []json.RawMessage     `json:"observed_queue_accounting"`
	Coverage                *identityCoverage     `json:"coverage"`
}

type identityDataset struct {
	Map               productIdentityMap
	Path              string
	SHA256            string
	AttestationPath   string
	AttestationSHA256 string
}

type identityMatch struct {
	MatchKind                    string                  `json:"match_kind"`
	ProductKey                   string                  `json:"product_key,omitempty"`
	JID                          string                  `json:"jid,omitempty"`
	CanonicalName                string                  `json:"canonical_name,omitempty"`
	ProductState                 string                  `json:"product_state,omitempty"`
	PriceSKUKey                  string                  `json:"price_sku_key,omitempty"`
	SourceNamespace              string                  `json:"source_namespace,omitempty"`
	SourceProductCode            string                  `json:"source_product_code,omitempty"`
	DisplayName                  string                  `json:"display_name,omitempty"`
	PriceMembershipRole          string                  `json:"price_membership_role,omitempty"`
	ListingKey                   string                  `json:"listing_key,omitempty"`
	Platform                     string                  `json:"platform,omitempty"`
	ListingID                    string                  `json:"listing_id,omitempty"`
	ListingIDKind                string                  `json:"listing_id_kind,omitempty"`
	ListingTitle                 string                  `json:"listing_title,omitempty"`
	ListingPack                  json.RawMessage         `json:"listing_pack,omitempty"`
	ResolutionID                 string                  `json:"resolution_id,omitempty"`
	ResolutionState              string                  `json:"resolution_state,omitempty"`
	VerificationMethod           string                  `json:"verification_method,omitempty"`
	VerifiedBy                   string                  `json:"verified_by,omitempty"`
	VerifiedAt                   string                  `json:"verified_at,omitempty"`
	ResolutionEvidence           json.RawMessage         `json:"resolution_evidence,omitempty"`
	CompanyCode                  string                  `json:"company_code,omitempty"`
	SAPSchema                    string                  `json:"sap_schema,omitempty"`
	FactoryItemKey               string                  `json:"factory_item_key,omitempty"`
	FactoryItemCode              string                  `json:"factory_item_code,omitempty"`
	FactoryItemName              string                  `json:"factory_item_name,omitempty"`
	FactoryItemClass             string                  `json:"factory_item_class,omitempty"`
	BindingRole                  string                  `json:"binding_role,omitempty"`
	FactoryBindingEvidence       json.RawMessage         `json:"factory_binding_evidence,omitempty"`
	PrimaryForScope              *bool                   `json:"primary_for_scope,omitempty"`
	FactoryUOMPerListingOffer    **identityRatio         `json:"factory_uom_per_listing_offer,omitempty"`
	ConversionState              string                  `json:"conversion_state,omitempty"`
	FactoryAccountingDisposition string                  `json:"factory_accounting_disposition,omitempty"`
	FactoryAccountingReason      string                  `json:"factory_accounting_reason,omitempty"`
	FactoryCollisionRelation     string                  `json:"factory_collision_relation,omitempty"`
	FactoryCollisionEvidence     json.RawMessage         `json:"factory_collision_evidence,omitempty"`
	FactoryMappingState          string                  `json:"factory_mapping_state,omitempty"`
	FactoryAbsence               *identityFactoryAbsence `json:"factory_absence,omitempty"`
}

type identityCatalogEntry struct {
	CompanyCode       string   `json:"company_code"`
	SAPSchema         string   `json:"sap_schema"`
	FactoryItemKey    string   `json:"factory_item_key"`
	FactoryItemCode   string   `json:"factory_item_code"`
	FactoryItemName   string   `json:"factory_item_name"`
	FactoryItemClass  string   `json:"factory_item_class"`
	State             string   `json:"state"`
	Disposition       string   `json:"disposition"`
	DispositionReason string   `json:"disposition_reason,omitempty"`
	ProductKeys       []string `json:"product_keys"`
	CanonicalJIDs     []string `json:"canonical_jids"`
	PriceSKUKeys      []string `json:"price_sku_keys"`
	ListingKeys       []string `json:"listing_keys"`
}

type identityFactoryAccounting struct {
	FactoryItemKey string          `json:"factory_item_key"`
	Disposition    string          `json:"disposition"`
	ListingKeys    []string        `json:"listing_keys"`
	Reason         string          `json:"reason"`
	Evidence       json.RawMessage `json:"evidence"`
}

type identityJIDAlias struct {
	AliasJID     string          `json:"alias_jid"`
	CanonicalJID string          `json:"canonical_jid"`
	Relation     string          `json:"relation"`
	DecisionID   string          `json:"decision_id"`
	Reason       string          `json:"reason"`
	Evidence     json.RawMessage `json:"evidence"`
}

type identityJIDConflict struct {
	ConflictID          string          `json:"conflict_id"`
	Kind                string          `json:"kind"`
	InvolvedJIDs        []string        `json:"involved_jids"`
	InvolvedListingKeys []string        `json:"involved_listing_keys"`
	Status              string          `json:"status"`
	Blocking            *bool           `json:"blocking"`
	ResolutionKind      string          `json:"resolution_kind"`
	Reason              string          `json:"reason"`
	Evidence            json.RawMessage `json:"evidence"`
}

type identityFactoryCodeCollision struct {
	ItemCode         string          `json:"item_code"`
	FactoryItemKeys  []string        `json:"factory_item_keys"`
	PhysicalRelation string          `json:"physical_relation"`
	Evidence         json.RawMessage `json:"evidence"`
}

type identityQueueAccounting struct {
	SourceSection string          `json:"source_section"`
	SourceIndex   *int            `json:"source_index"`
	EntryKind     string          `json:"entry_kind"`
	Platform      json.RawMessage `json:"platform"`
	ListingID     json.RawMessage `json:"listing_id"`
	Disposition   string          `json:"disposition"`
	Evidence      json.RawMessage `json:"evidence"`
}

type identityCommandOptions struct {
	mapPath      string
	allCompanies bool
	limit        int
}

func newProductCmd(flags *rootFlags) *cobra.Command {
	opts := &identityCommandOptions{}
	cmd := &cobra.Command{
		Use:         "product",
		Short:       "Resolve the shared, read-only product identity map",
		Annotations: map[string]string{"mcp:read-only": "true"},
		Long: `Resolve marketplace listing IDs, price SKU keys, JIDs, and
company-qualified Factory items through JivoGPT's released identity map.

This command reads a local artifact only. It never calls or mutates the
Factory API. Bare Factory item codes require an explicit --company because
the same code can identify different products in different companies.`,
		RunE: parentNoSubcommandRunE(flags),
	}
	cmd.PersistentFlags().StringVar(&opts.mapPath, "identity-map", "", "Path to product-identity-map.json (or set JIVO_PRODUCT_IDENTITY_MAP)")
	cmd.AddCommand(newProductResolveCmd(flags, opts))
	cmd.AddCommand(newProductSearchCmd(flags, opts))
	cmd.AddCommand(newProductCatalogCmd(flags, opts))
	cmd.AddCommand(newProductVerifyCmd(flags, opts))
	cmd.AddCommand(newProductCoverageCmd(flags, opts))
	return cmd
}

func newProductResolveCmd(flags *rootFlags, opts *identityCommandOptions) *cobra.Command {
	cmd := &cobra.Command{
		Use:         "resolve <IDENTIFIER>",
		Short:       "Resolve an exact scraper code, JID, listing ID/key, price SKU key, or Factory key",
		Annotations: map[string]string{"mcp:read-only": "true"},
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) != 1 {
				return usageErr(fmt.Errorf("resolve requires exactly one identifier"))
			}
			if dryRunOK(flags) {
				return nil
			}
			if opts.allCompanies && flags.companyExplicit {
				return usageErr(fmt.Errorf("--all-companies cannot be combined with --company or JIVO_FACTORY_COMPANY"))
			}
			dataset, err := loadIdentityDataset(opts.mapPath)
			if err != nil {
				return err
			}
			kind, rows, err := dataset.resolveExact(args[0], flags, opts.allCompanies)
			if err != nil {
				return err
			}
			return printJSONFiltered(cmd.OutOrStdout(), dataset.envelope(map[string]any{
				"identifier":      args[0],
				"identifier_kind": kind,
				"matches":         rows,
			}), flags)
		},
	}
	cmd.Flags().BoolVar(&opts.allCompanies, "all-companies", false, "Return every company-qualified Factory match for a bare item code")
	return cmd
}

func newProductSearchCmd(flags *rootFlags, opts *identityCommandOptions) *cobra.Command {
	cmd := &cobra.Command{
		Use:         "search <TEXT>",
		Short:       "Search product names and titles without using text as an identity join",
		Annotations: map[string]string{"mcp:read-only": "true"},
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) == 0 || strings.TrimSpace(strings.Join(args, " ")) == "" {
				return usageErr(fmt.Errorf("search requires non-empty text"))
			}
			if dryRunOK(flags) {
				return nil
			}
			dataset, err := loadIdentityDataset(opts.mapPath)
			if err != nil {
				return err
			}
			query := strings.Join(args, " ")
			rows := dataset.search(query, flags)
			if len(rows) == 0 {
				return notFoundErr(fmt.Errorf("no product identity text matches for %q", query))
			}
			if opts.limit > 0 && len(rows) > opts.limit {
				rows = rows[:opts.limit]
			}
			return printJSONFiltered(cmd.OutOrStdout(), dataset.envelope(map[string]any{
				"query":   query,
				"count":   len(rows),
				"matches": rows,
			}), flags)
		},
	}
	cmd.Flags().IntVar(&opts.limit, "limit", 50, "Maximum result rows (0 returns all)")
	return cmd
}

func newProductCatalogCmd(flags *rootFlags, opts *identityCommandOptions) *cobra.Command {
	return &cobra.Command{
		Use:         "catalog",
		Short:       "List the qualified Factory product catalog for one explicit company",
		Annotations: map[string]string{"mcp:read-only": "true"},
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) != 0 {
				return usageErr(fmt.Errorf("catalog takes no positional arguments"))
			}
			if dryRunOK(flags) {
				return nil
			}
			if !flags.companyExplicit {
				return usageErr(fmt.Errorf("product catalog requires --company (or JIVO_FACTORY_COMPANY); the JIVO_MART API default is not an identity scope"))
			}
			dataset, err := loadIdentityDataset(opts.mapPath)
			if err != nil {
				return err
			}
			items := dataset.catalog(flags.companyCode)
			if len(items) == 0 {
				return notFoundErr(fmt.Errorf("no Factory identity items for company %s", flags.companyCode))
			}
			return printJSONFiltered(cmd.OutOrStdout(), dataset.envelope(map[string]any{
				"company_code": flags.companyCode,
				"count":        len(items),
				"items":        items,
			}), flags)
		},
	}
}

func newProductVerifyCmd(flags *rootFlags, opts *identityCommandOptions) *cobra.Command {
	return &cobra.Command{
		Use:         "verify",
		Short:       "Fail closed unless the identity map is released and complete",
		Annotations: map[string]string{"mcp:read-only": "true"},
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) != 0 {
				return usageErr(fmt.Errorf("verify takes no positional arguments"))
			}
			if dryRunOK(flags) {
				return nil
			}
			dataset, err := loadIdentityDataset(opts.mapPath)
			if err != nil {
				return err
			}
			return printJSONFiltered(cmd.OutOrStdout(), dataset.envelope(map[string]any{
				"valid":          true,
				"release_status": dataset.Map.Contract.ReleaseStatus,
				"read_only":      true,
				"counts":         dataset.actualCounts(),
			}), flags)
		},
	}
}

func newProductCoverageCmd(flags *rootFlags, opts *identityCommandOptions) *cobra.Command {
	return &cobra.Command{
		Use:         "coverage",
		Short:       "Show the released map's zero-gap coverage gate",
		Annotations: map[string]string{"mcp:read-only": "true"},
		RunE: func(cmd *cobra.Command, args []string) error {
			if len(args) != 0 {
				return usageErr(fmt.Errorf("coverage takes no positional arguments"))
			}
			if dryRunOK(flags) {
				return nil
			}
			dataset, err := loadIdentityDataset(opts.mapPath)
			if err != nil {
				return err
			}
			coverage, err := normalizedCoverage(dataset.Map.Coverage)
			if err != nil { // loadIdentityDataset already validates; keep fail-closed locally too.
				return identityMapErr(err)
			}
			return printJSONFiltered(cmd.OutOrStdout(), dataset.envelope(map[string]any{
				"coverage":      coverage,
				"actual_counts": dataset.actualCounts(),
			}), flags)
		},
	}
}

// identityReleaseTrustTestHook is nil in production builds. Package tests may
// use it to trust one exact synthetic fixture without adding a CLI flag, env
// variable, or production digest that could bypass the release anchor.
var identityReleaseTrustTestHook func(mapPath string, mapRaw []byte) (*identityReleaseTrust, bool, error)

func loadIdentityDataset(explicitPath string) (*identityDataset, error) {
	path, err := resolveIdentityMapPath(explicitPath)
	if err != nil {
		return nil, identityMapErr(err)
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, identityMapErr(fmt.Errorf("read product identity map %s: %w", path, err))
	}
	if err := rejectDuplicateIdentityJSONKeys(raw); err != nil {
		return nil, identityMapErr(fmt.Errorf("invalid product identity JSON %s: %w", path, err))
	}
	var m productIdentityMap
	if err := json.Unmarshal(raw, &m); err != nil {
		return nil, identityMapErr(fmt.Errorf("invalid product identity JSON %s: %w", path, err))
	}
	if err := validateProductIdentityMap(&m); err != nil {
		return nil, identityMapErr(fmt.Errorf("product identity map rejected: %w", err))
	}
	trust, err := verifyTrustedIdentityRelease(path, raw, &m)
	if err != nil {
		return nil, identityMapErr(fmt.Errorf("product identity release rejected: %w", err))
	}
	sum := sha256.Sum256(raw)
	return &identityDataset{
		Map:               m,
		Path:              path,
		SHA256:            hex.EncodeToString(sum[:]),
		AttestationPath:   trust.Path,
		AttestationSHA256: trust.SHA256,
	}, nil
}

func verifyTrustedIdentityRelease(mapPath string, mapRaw []byte, m *productIdentityMap) (*identityReleaseTrust, error) {
	if identityReleaseTrustTestHook != nil {
		if trust, handled, err := identityReleaseTrustTestHook(mapPath, mapRaw); handled {
			return trust, err
		}
	}

	attestationPath := filepath.Join(filepath.Dir(mapPath), identityAttestationFilename)
	attestationRaw, err := os.ReadFile(attestationPath)
	if err != nil {
		return nil, fmt.Errorf("read detached attestation %s: %w", attestationPath, err)
	}
	if err := rejectDuplicateIdentityJSONKeys(attestationRaw); err != nil {
		return nil, fmt.Errorf("invalid detached attestation %s: %w", attestationPath, err)
	}
	var attestation identityReleaseAttestation
	decoder := json.NewDecoder(bytes.NewReader(attestationRaw))
	decoder.DisallowUnknownFields()
	if err := decoder.Decode(&attestation); err != nil {
		return nil, fmt.Errorf("invalid detached attestation %s: %w", attestationPath, err)
	}
	if token, err := decoder.Token(); err != io.EOF {
		if err != nil {
			return nil, fmt.Errorf("invalid detached attestation trailing data: %w", err)
		}
		return nil, fmt.Errorf("unexpected detached attestation trailing token %v", token)
	}

	attestationSHA := identityPrefixedSHA256(attestationRaw)
	if attestationSHA != identityTrustedAttestationSHA256 {
		return nil, fmt.Errorf("detached attestation digest %s is not the compiled trusted release %s", attestationSHA, identityTrustedAttestationSHA256)
	}
	if attestation.FormatVersion != identityAttestationFormatVersion {
		return nil, fmt.Errorf("unsupported attestation format_version %q", attestation.FormatVersion)
	}
	if attestation.ContractName != identityAttestationContractName || m.Contract.Name != identityContractName {
		return nil, fmt.Errorf("attestation contract_name %q or map contract %q is unsupported", attestation.ContractName, m.Contract.Name)
	}
	if attestation.DatasetVersion != m.Contract.DatasetVersion || attestation.SchemaVersion != m.Contract.SchemaVersion || attestation.ReleaseStatus != m.Contract.ReleaseStatus {
		return nil, fmt.Errorf("attestation contract metadata disagrees with map release")
	}
	if attestation.ReleaseStatus != "released" {
		return nil, fmt.Errorf("attestation release_status=%q, want released", attestation.ReleaseStatus)
	}
	if attestation.Map.URI != identityMapFilename() {
		return nil, fmt.Errorf("attestation map.uri=%q, want %s", attestation.Map.URI, identityMapFilename())
	}
	mapSHA := identityPrefixedSHA256(mapRaw)
	if !validIdentitySHA256(attestation.Map.SHA256) || attestation.Map.SHA256 != mapSHA {
		return nil, fmt.Errorf("map digest %s does not match attested digest %s", mapSHA, attestation.Map.SHA256)
	}
	if attestation.Verification.VerifierVersion == "" || attestation.Verification.CheckCount <= 0 {
		return nil, fmt.Errorf("attestation verification proof is incomplete")
	}

	expectedArtifacts := make(map[string]identitySource, len(m.Sources))
	for position, rawSource := range m.Sources {
		var source identitySource
		if err := json.Unmarshal(rawSource, &source); err != nil {
			return nil, fmt.Errorf("sources[%d] is not a valid source record: %w", position, err)
		}
		if source.SourceID == "" {
			return nil, fmt.Errorf("sources[%d] has no source_id", position)
		}
		if _, duplicate := expectedArtifacts[source.SourceID]; duplicate {
			return nil, fmt.Errorf("sources repeats source_id %q", source.SourceID)
		}
		expectedArtifacts[source.SourceID] = source
	}
	if len(attestation.EvidenceArtifacts) != len(expectedArtifacts) {
		return nil, fmt.Errorf("attestation has %d evidence artifacts, want %d map sources", len(attestation.EvidenceArtifacts), len(expectedArtifacts))
	}
	seenSources := map[string]struct{}{}
	seenURIs := map[string]struct{}{}
	for position, artifact := range attestation.EvidenceArtifacts {
		source, exists := expectedArtifacts[artifact.SourceID]
		if !exists {
			return nil, fmt.Errorf("attestation evidence_artifacts[%d] has unknown source_id %q", position, artifact.SourceID)
		}
		if _, duplicate := seenSources[artifact.SourceID]; duplicate {
			return nil, fmt.Errorf("attestation repeats source_id %q", artifact.SourceID)
		}
		seenSources[artifact.SourceID] = struct{}{}
		if !validIdentitySHA256(artifact.SHA256) || artifact.SHA256 != source.ContentSHA256 {
			return nil, fmt.Errorf("attestation digest for source %q disagrees with map source manifest", artifact.SourceID)
		}
		expectedURI := identityPortableSourceURI(source)
		if artifact.URI != expectedURI {
			return nil, fmt.Errorf("attestation source %q uri=%q, want %q", artifact.SourceID, artifact.URI, expectedURI)
		}
		if _, duplicate := seenURIs[artifact.URI]; duplicate {
			return nil, fmt.Errorf("attestation repeats evidence uri %q", artifact.URI)
		}
		seenURIs[artifact.URI] = struct{}{}
		artifactPath, err := resolveIdentityAttestationArtifact(attestationPath, artifact.URI)
		if err != nil {
			return nil, fmt.Errorf("attestation source %q: %w", artifact.SourceID, err)
		}
		artifactRaw, err := os.ReadFile(artifactPath)
		if err != nil {
			return nil, fmt.Errorf("read attested source %q at %s: %w", artifact.SourceID, artifactPath, err)
		}
		if actual := identityPrefixedSHA256(artifactRaw); actual != artifact.SHA256 {
			return nil, fmt.Errorf("attested source %q digest drift: got %s want %s", artifact.SourceID, actual, artifact.SHA256)
		}
	}

	return &identityReleaseTrust{Path: attestationPath, SHA256: attestationSHA}, nil
}

func identityMapFilename() string { return filepath.Base(identityDefaultRelativeMap) }

func identityPrefixedSHA256(raw []byte) string {
	sum := sha256.Sum256(raw)
	return "sha256:" + hex.EncodeToString(sum[:])
}

func identityPortableSourceURI(source identitySource) string {
	if source.SourceID == "review-decisions" {
		return "review-decisions.json"
	}
	return filepath.ToSlash(filepath.Join("sources", filepath.Base(filepath.FromSlash(source.URI))))
}

func resolveIdentityAttestationArtifact(attestationPath, uri string) (string, error) {
	if uri == "" || filepath.IsAbs(uri) || strings.Contains(uri, `\`) {
		return "", fmt.Errorf("unsafe relative artifact uri %q", uri)
	}
	clean := filepath.Clean(filepath.FromSlash(uri))
	if clean == "." || clean == ".." || strings.HasPrefix(clean, ".."+string(os.PathSeparator)) || filepath.ToSlash(clean) != uri {
		return "", fmt.Errorf("unsafe relative artifact uri %q", uri)
	}
	base, err := filepath.EvalSymlinks(filepath.Dir(attestationPath))
	if err != nil {
		return "", fmt.Errorf("resolve attestation directory: %w", err)
	}
	candidate := filepath.Join(base, clean)
	resolved, err := filepath.EvalSymlinks(candidate)
	if err != nil {
		return "", fmt.Errorf("resolve artifact %q: %w", uri, err)
	}
	relative, err := filepath.Rel(base, resolved)
	if err != nil || relative == ".." || strings.HasPrefix(relative, ".."+string(os.PathSeparator)) {
		return "", fmt.Errorf("artifact uri %q escapes the release directory", uri)
	}
	return resolved, nil
}

func rejectDuplicateIdentityJSONKeys(raw []byte) error {
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if err := walkIdentityJSONValue(decoder, "$"); err != nil {
		return err
	}
	if token, err := decoder.Token(); err != io.EOF {
		if err != nil {
			return fmt.Errorf("invalid trailing JSON: %w", err)
		}
		return fmt.Errorf("unexpected trailing JSON token %v", token)
	}
	return nil
}

func walkIdentityJSONValue(decoder *json.Decoder, path string) error {
	token, err := decoder.Token()
	if err != nil {
		return fmt.Errorf("invalid JSON at %s: %w", path, err)
	}
	delimiter, composite := token.(json.Delim)
	if !composite {
		return nil
	}
	switch delimiter {
	case '{':
		seen := map[string]struct{}{}
		for decoder.More() {
			keyToken, err := decoder.Token()
			if err != nil {
				return fmt.Errorf("invalid object key at %s: %w", path, err)
			}
			key, ok := keyToken.(string)
			if !ok {
				return fmt.Errorf("non-string object key at %s", path)
			}
			if _, duplicate := seen[key]; duplicate {
				return fmt.Errorf("duplicate object key %q at %s", key, path)
			}
			seen[key] = struct{}{}
			if err := walkIdentityJSONValue(decoder, path+"."+key); err != nil {
				return err
			}
		}
		end, err := decoder.Token()
		if err != nil || end != json.Delim('}') {
			return fmt.Errorf("unterminated object at %s", path)
		}
	case '[':
		index := 0
		for decoder.More() {
			if err := walkIdentityJSONValue(decoder, fmt.Sprintf("%s[%d]", path, index)); err != nil {
				return err
			}
			index++
		}
		end, err := decoder.Token()
		if err != nil || end != json.Delim(']') {
			return fmt.Errorf("unterminated array at %s", path)
		}
	default:
		return fmt.Errorf("unexpected JSON delimiter %q at %s", delimiter, path)
	}
	return nil
}

func resolveIdentityMapPath(explicitPath string) (string, error) {
	selected := strings.TrimSpace(explicitPath)
	if selected == "" {
		selected = strings.TrimSpace(os.Getenv("JIVO_PRODUCT_IDENTITY_MAP"))
	}
	if selected != "" {
		abs, err := filepath.Abs(selected)
		if err != nil {
			return "", fmt.Errorf("resolve identity map path %q: %w", selected, err)
		}
		return abs, nil
	}

	candidates := make([]string, 0, 20)
	if cwd, err := os.Getwd(); err == nil {
		for dir, depth := cwd, 0; depth < 10; depth++ {
			candidates = append(candidates,
				filepath.Join(dir, identityDefaultRelativeMap),
				filepath.Join(dir, "product-identity", "v1", "product-identity-map.json"),
			)
			parent := filepath.Dir(dir)
			if parent == dir {
				break
			}
			dir = parent
		}
	}
	if executable, err := os.Executable(); err == nil {
		base := filepath.Dir(executable)
		candidates = append(candidates,
			filepath.Join(base, identityDefaultRelativeMap),
			filepath.Join(base, "..", "product-identity", "v1", "product-identity-map.json"),
			filepath.Join(base, "..", "..", identityDefaultRelativeMap),
		)
	}
	seen := map[string]struct{}{}
	for _, candidate := range candidates {
		candidate = filepath.Clean(candidate)
		if _, ok := seen[candidate]; ok {
			continue
		}
		seen[candidate] = struct{}{}
		if info, err := os.Stat(candidate); err == nil && !info.IsDir() {
			abs, _ := filepath.Abs(candidate)
			return abs, nil
		}
	}
	return "", fmt.Errorf("released product identity map not found; pass --identity-map, set JIVO_PRODUCT_IDENTITY_MAP, or provide %s", identityDefaultRelativeMap)
}

func validateProductIdentityMap(m *productIdentityMap) error {
	if m == nil {
		return fmt.Errorf("map is null")
	}
	c := m.Contract
	if c.Name != identityContractName {
		return fmt.Errorf("contract.name must be %q", identityContractName)
	}
	parts := strings.Split(c.SchemaVersion, ".")
	if len(parts) < 1 || parts[0] == "" {
		return fmt.Errorf("contract.schema_version is required")
	}
	major, err := strconv.Atoi(parts[0])
	if err != nil {
		return fmt.Errorf("invalid contract.schema_version %q", c.SchemaVersion)
	}
	if major != identitySupportedMajor {
		return fmt.Errorf("unsupported product identity schema major %d (supported: %d)", major, identitySupportedMajor)
	}
	if c.DatasetVersion == "" || c.GeneratedAt == "" || c.GeneratorVersion == "" {
		return fmt.Errorf("contract dataset_version, generated_at, and generator_version are required")
	}
	if c.ReleaseStatus != "released" {
		return fmt.Errorf("contract.release_status is %q, want released", c.ReleaseStatus)
	}
	if c.ReadOnly == nil || !*c.ReadOnly {
		return fmt.Errorf("contract.read_only must be true")
	}
	if len(m.Sources) == 0 || len(m.FactoryScopes) == 0 || len(m.Products) == 0 || len(m.PriceSKUs) == 0 || len(m.Listings) == 0 || len(m.FactoryItems) == 0 || len(m.Resolutions) == 0 {
		return fmt.Errorf("released map must include non-empty sources, factory_scopes, products, price_skus, listings, factory_items, and resolutions")
	}
	if m.JIDAliases == nil || m.JIDConflicts == nil || m.FactoryItemAccounting == nil || m.FactoryCodeCollisions == nil || m.ObservedQueueAccounting == nil {
		return fmt.Errorf("released map is missing one or more accounting arrays")
	}
	sourceIDs, err := identitySourceIDs(m.Sources)
	if err != nil {
		return err
	}

	products := map[string]identityProduct{}
	productsByJID := map[string]string{}
	for _, p := range m.Products {
		if p.ProductKey == "" || p.CanonicalName == "" || p.State == "" {
			return fmt.Errorf("every product requires product_key, canonical_name, and state")
		}
		switch p.State {
		case "active", "retired", "merged", "split":
		default:
			return fmt.Errorf("product %q has unsupported state %q", p.ProductKey, p.State)
		}
		if p.JID != "" {
			expectedKey := "urn:jivo:product:" + identityPercentEncode(p.JID)
			if p.ProductKey != expectedKey {
				return fmt.Errorf("product key %q disagrees with jid %q; want %q", p.ProductKey, p.JID, expectedKey)
			}
		} else if !strings.HasPrefix(p.ProductKey, "urn:jivo:product:local:") {
			return fmt.Errorf("nullable-JID product key %q must use the urn:jivo:product:local namespace", p.ProductKey)
		}
		if _, exists := products[p.ProductKey]; exists {
			return fmt.Errorf("duplicate product_key %q", p.ProductKey)
		}
		if _, err := validateIdentityEvidence(p.Evidence, "product "+p.ProductKey, sourceIDs, 1); err != nil {
			return err
		}
		products[p.ProductKey] = p
		if p.JID != "" {
			if prior, exists := productsByJID[p.JID]; exists {
				return fmt.Errorf("duplicate product jid %q in %q and %q", p.JID, prior, p.ProductKey)
			}
			productsByJID[p.JID] = p.ProductKey
		}
	}

	priceSKUs := map[string]identityPriceSKU{}
	priceSourceIdentities := map[string]string{}
	for _, p := range m.PriceSKUs {
		if p.PriceSKUKey == "" || p.SourceNamespace == "" || p.SourceProductCode == "" || p.DisplayName == "" || p.State == "" || p.MemberListingKeys == nil {
			return fmt.Errorf("every price_sku requires its key, source identity, display_name, state, and member_listing_keys")
		}
		if _, exists := priceSKUs[p.PriceSKUKey]; exists {
			return fmt.Errorf("duplicate price_sku_key %q", p.PriceSKUKey)
		}
		switch p.State {
		case "active", "retired", "excluded_non_product":
		default:
			return fmt.Errorf("price_sku %q has unsupported state %q", p.PriceSKUKey, p.State)
		}
		expectedKey := "urn:jivo:price-sku:" + identityPercentEncode(p.SourceNamespace) + ":" + identityPercentEncode(p.SourceProductCode)
		if p.PriceSKUKey != expectedKey {
			return fmt.Errorf("price_sku key %q disagrees with source identity; want %q", p.PriceSKUKey, expectedKey)
		}
		if _, err := validateIdentityEvidence(p.Evidence, "price_sku "+p.PriceSKUKey, sourceIDs, 1); err != nil {
			return err
		}
		sourceIdentity := p.SourceNamespace + "\x00" + p.SourceProductCode
		if prior, exists := priceSourceIdentities[sourceIdentity]; exists {
			return fmt.Errorf("price_skus %q and %q duplicate source identity (%s, %s)", prior, p.PriceSKUKey, p.SourceNamespace, p.SourceProductCode)
		}
		priceSourceIdentities[sourceIdentity] = p.PriceSKUKey
		priceSKUs[p.PriceSKUKey] = p
	}

	listings := map[string]identityListing{}
	listingIdentity := map[string]string{}
	for _, listing := range m.Listings {
		if listing.ListingKey == "" || listing.PriceSKUKey == "" || len(listing.PriceSKUKeys) == 0 || len(listing.SourceMemberships) == 0 || listing.Platform == "" || listing.ListingID == "" || listing.ListingIDKind == "" || listing.Title == "" || listing.State == "" || listing.IsPrimary == nil {
			return fmt.Errorf("every listing requires its key, price SKU, platform identity, title, and state")
		}
		if _, exists := listings[listing.ListingKey]; exists {
			return fmt.Errorf("duplicate listing_key %q", listing.ListingKey)
		}
		switch listing.State {
		case "active", "retired", "excluded_non_product":
		default:
			return fmt.Errorf("listing %q has unsupported state %q", listing.ListingKey, listing.State)
		}
		expectedKey := "urn:jivo:listing:" + identityPercentEncode(listing.Platform) + ":" + identityPercentEncode(listing.ListingID)
		if listing.ListingKey != expectedKey {
			return fmt.Errorf("listing key %q disagrees with platform/listing_id; want %q", listing.ListingKey, expectedKey)
		}
		membershipKeys := map[string]struct{}{}
		for _, key := range listing.PriceSKUKeys {
			if _, duplicate := membershipKeys[key]; duplicate {
				return fmt.Errorf("listing %q repeats price_sku_key %q", listing.ListingKey, key)
			}
			if _, exists := priceSKUs[key]; !exists {
				return fmt.Errorf("listing %q references unknown price_sku_key %q", listing.ListingKey, key)
			}
			membershipKeys[key] = struct{}{}
		}
		if _, exists := membershipKeys[listing.PriceSKUKey]; !exists {
			return fmt.Errorf("listing %q legacy price_sku_key %q is absent from price_sku_keys", listing.ListingKey, listing.PriceSKUKey)
		}
		sourceMembershipKeys := map[string]struct{}{}
		hasPrimaryMembership := false
		for _, membership := range listing.SourceMemberships {
			if membership.PriceSKUKey == "" || (membership.Role != "primary" && membership.Role != "alternate") {
				return fmt.Errorf("listing %q has an invalid source_membership", listing.ListingKey)
			}
			if _, duplicate := sourceMembershipKeys[membership.PriceSKUKey]; duplicate {
				return fmt.Errorf("listing %q repeats source_membership for %q", listing.ListingKey, membership.PriceSKUKey)
			}
			sourceMembershipKeys[membership.PriceSKUKey] = struct{}{}
			if membership.Role == "primary" {
				hasPrimaryMembership = true
			}
		}
		if len(sourceMembershipKeys) != len(membershipKeys) {
			return fmt.Errorf("listing %q price_sku_keys and source_memberships differ", listing.ListingKey)
		}
		for key := range membershipKeys {
			if _, exists := sourceMembershipKeys[key]; !exists {
				return fmt.Errorf("listing %q source_memberships omits price_sku_key %q", listing.ListingKey, key)
			}
		}
		if *listing.IsPrimary != hasPrimaryMembership {
			return fmt.Errorf("listing %q is_primary disagrees with source_membership roles", listing.ListingKey)
		}
		if err := validateIdentityPack(listing.Pack, listing.ListingKey); err != nil {
			return err
		}
		if _, err := validateIdentityEvidence(listing.Evidence, "listing "+listing.ListingKey, sourceIDs, 1); err != nil {
			return err
		}
		qualified := listing.Platform + "\x00" + listing.ListingID
		if prior, exists := listingIdentity[qualified]; exists {
			return fmt.Errorf("duplicate qualified listing identity (%s, %s) in %q and %q", listing.Platform, listing.ListingID, prior, listing.ListingKey)
		}
		listingIdentity[qualified] = listing.ListingKey
		listings[listing.ListingKey] = listing
	}
	for _, p := range m.PriceSKUs {
		members := map[string]struct{}{}
		for _, key := range p.MemberListingKeys {
			listing, exists := listings[key]
			if !exists {
				return fmt.Errorf("price_sku %q references unknown listing %q", p.PriceSKUKey, key)
			}
			if !containsString(listing.PriceSKUKeys, p.PriceSKUKey) {
				return fmt.Errorf("price_sku/listing reverse reference mismatch for %q", key)
			}
			if _, duplicate := members[key]; duplicate {
				return fmt.Errorf("price_sku %q repeats listing %q", p.PriceSKUKey, key)
			}
			members[key] = struct{}{}
		}
		if strings.EqualFold(p.State, "active") && len(members) == 0 {
			return fmt.Errorf("active price_sku %q has no member listings", p.PriceSKUKey)
		}
	}
	for _, listing := range m.Listings {
		for _, priceSKUKey := range listing.PriceSKUKeys {
			if !containsString(priceSKUs[priceSKUKey].MemberListingKeys, listing.ListingKey) {
				return fmt.Errorf("listing %q is missing from price_sku %q member_listing_keys", listing.ListingKey, priceSKUKey)
			}
		}
	}

	factoryScopes, err := identityFactoryScopeDetails(m.FactoryScopes)
	if err != nil {
		return err
	}
	if len(factoryScopes) != 3 {
		return fmt.Errorf("released map must declare all 3 Factory scopes; found %d", len(factoryScopes))
	}
	factoryItems := map[string]identityFactoryItem{}
	qualifiedFactory := map[string]string{}
	for _, item := range m.FactoryItems {
		if item.FactoryItemKey == "" || item.FactoryScopeKey == "" || item.CompanyCode == "" || item.SAPSchema == "" || item.ItemCode == "" || item.ItemName == "" || item.ItemClass == "" || item.State == "" {
			return fmt.Errorf("every factory_item requires its qualified key, scope, company, schema, code, name, class, and state")
		}
		if _, exists := factoryItems[item.FactoryItemKey]; exists {
			return fmt.Errorf("duplicate factory_item_key %q", item.FactoryItemKey)
		}
		expectedKey := "urn:jivo:factory:" + identityPercentEncode(item.CompanyCode) + ":" + identityPercentEncode(item.SAPSchema) + ":" + identityPercentEncode(item.ItemCode)
		if item.FactoryItemKey != expectedKey {
			return fmt.Errorf("factory_item key %q disagrees with company/schema/code; want %q", item.FactoryItemKey, expectedKey)
		}
		switch item.ItemClass {
		case "retail_finished_good", "bundle", "component", "raw_material", "packaging", "other":
		default:
			return fmt.Errorf("factory_item %q has unsupported item_class %q", item.FactoryItemKey, item.ItemClass)
		}
		if item.State != "active" && item.State != "inactive" {
			return fmt.Errorf("factory_item %q has unsupported state %q", item.FactoryItemKey, item.State)
		}
		if _, err := validateIdentityEvidence(item.Evidence, "factory_item "+item.FactoryItemKey, sourceIDs, 1); err != nil {
			return err
		}
		scope, exists := factoryScopes[item.FactoryScopeKey]
		if !exists {
			return fmt.Errorf("factory_item %q references unknown factory_scope_key %q", item.FactoryItemKey, item.FactoryScopeKey)
		}
		if scope.CompanyCode != item.CompanyCode || scope.SAPSchema != item.SAPSchema {
			return fmt.Errorf("factory_item %q company/schema disagrees with scope %q", item.FactoryItemKey, item.FactoryScopeKey)
		}
		qualified := item.CompanyCode + "\x00" + item.SAPSchema + "\x00" + item.ItemCode
		if prior, exists := qualifiedFactory[qualified]; exists {
			return fmt.Errorf("duplicate qualified Factory identity in %q and %q", prior, item.FactoryItemKey)
		}
		qualifiedFactory[qualified] = item.FactoryItemKey
		factoryItems[item.FactoryItemKey] = item
	}

	resolutionByListing := map[string]int{}
	resolutionIDs := map[string]struct{}{}
	for _, resolution := range m.Resolutions {
		if resolution.ResolutionID == "" || resolution.ListingKey == "" || resolution.CanonicalProductKey == "" || resolution.State == "" || resolution.FactoryMappingState == "" || resolution.VerificationMethod == "" || resolution.VerifiedBy == "" || resolution.VerifiedAt == "" {
			return fmt.Errorf("every resolution requires identity, state, and verification provenance")
		}
		if _, exists := resolutionIDs[resolution.ResolutionID]; exists {
			return fmt.Errorf("duplicate resolution_id %q", resolution.ResolutionID)
		}
		resolutionIDs[resolution.ResolutionID] = struct{}{}
		if _, exists := listings[resolution.ListingKey]; !exists {
			return fmt.Errorf("resolution %q references unknown listing %q", resolution.ResolutionID, resolution.ListingKey)
		}
		product, exists := products[resolution.CanonicalProductKey]
		if !exists {
			return fmt.Errorf("resolution %q references unknown canonical_product_key %q", resolution.ResolutionID, resolution.CanonicalProductKey)
		}
		if product.JID != resolution.CanonicalJID {
			return fmt.Errorf("resolution %q canonical_jid %q disagrees with product %q jid %q", resolution.ResolutionID, resolution.CanonicalJID, product.ProductKey, product.JID)
		}
		if resolution.State != "verified" && resolution.State != "retired" {
			return fmt.Errorf("resolution %q has unsupported state %q", resolution.ResolutionID, resolution.State)
		}
		if _, err := validateIdentityEvidence(resolution.Evidence, "resolution "+resolution.ResolutionID, sourceIDs, 1); err != nil {
			return err
		}
		resolutionByListing[resolution.ListingKey]++
		switch resolution.FactoryMappingState {
		case "verified":
			if len(resolution.FactoryBindings) == 0 {
				return fmt.Errorf("verified resolution %q has no Factory binding", resolution.ResolutionID)
			}
			if resolution.FactoryAbsence != nil {
				return fmt.Errorf("verified resolution %q must not declare factory_absence", resolution.ResolutionID)
			}
		case "reviewed_absent":
			if len(resolution.FactoryBindings) != 0 {
				return fmt.Errorf("reviewed_absent resolution %q must not contain Factory bindings", resolution.ResolutionID)
			}
			if err := validateFactoryAbsence(resolution.ResolutionID, resolution.FactoryAbsence, factoryScopes, sourceIDs); err != nil {
				return err
			}
		default:
			return fmt.Errorf("resolution %q has unsupported factory_mapping_state %q", resolution.ResolutionID, resolution.FactoryMappingState)
		}
		seenBindings := map[string]struct{}{}
		primariesPerScope := map[string]int{}
		for _, binding := range resolution.FactoryBindings {
			if binding.FactoryItemKey == "" || binding.Role == "" || binding.PrimaryForScope == nil || binding.ConversionState == "" {
				return fmt.Errorf("resolution %q has an incomplete Factory binding", resolution.ResolutionID)
			}
			switch binding.Role {
			case "sellable_unit", "bundle_parent", "bundle_component", "intercompany_equivalent":
			default:
				return fmt.Errorf("resolution %q binding %q has unsupported role %q", resolution.ResolutionID, binding.FactoryItemKey, binding.Role)
			}
			switch binding.ConversionState {
			case "verified":
				if binding.FactoryUOMPerListingOffer == nil || binding.FactoryUOMPerListingOffer.Numerator <= 0 || binding.FactoryUOMPerListingOffer.Denominator <= 0 {
					return fmt.Errorf("resolution %q binding %q has verified conversion without a positive ratio", resolution.ResolutionID, binding.FactoryItemKey)
				}
			case "not_proven":
				if binding.FactoryUOMPerListingOffer != nil {
					return fmt.Errorf("resolution %q binding %q has not_proven conversion with a ratio", resolution.ResolutionID, binding.FactoryItemKey)
				}
			default:
				return fmt.Errorf("resolution %q binding %q has unsupported conversion_state %q", resolution.ResolutionID, binding.FactoryItemKey, binding.ConversionState)
			}
			kinds, err := validateIdentityEvidence(binding.Evidence, "resolution "+resolution.ResolutionID+" Factory binding "+binding.FactoryItemKey, sourceIDs, 2)
			if err != nil {
				return err
			}
			if !kinds["qualified_factory_record"] || !(kinds["exact_listing_identity"] || kinds["exact_source_sap"] || kinds["exact_price_code"]) {
				return fmt.Errorf("resolution %q binding %q evidence must include an exact listing/source claim and qualified_factory_record", resolution.ResolutionID, binding.FactoryItemKey)
			}
			if _, exists := factoryItems[binding.FactoryItemKey]; !exists {
				return fmt.Errorf("resolution %q references unknown factory_item_key %q", resolution.ResolutionID, binding.FactoryItemKey)
			}
			if _, duplicate := seenBindings[binding.FactoryItemKey]; duplicate {
				return fmt.Errorf("resolution %q repeats factory_item_key %q", resolution.ResolutionID, binding.FactoryItemKey)
			}
			seenBindings[binding.FactoryItemKey] = struct{}{}
			item := factoryItems[binding.FactoryItemKey]
			if *binding.PrimaryForScope {
				primariesPerScope[item.FactoryScopeKey]++
			}
		}
		for scope, count := range primariesPerScope {
			if count > 1 {
				return fmt.Errorf("resolution %q has %d primary bindings in Factory scope %q; want at most 1", resolution.ResolutionID, count, scope)
			}
		}
	}
	for _, listing := range m.Listings {
		if resolutionByListing[listing.ListingKey] != 1 {
			return fmt.Errorf("listing %q has %d resolutions, want exactly 1", listing.ListingKey, resolutionByListing[listing.ListingKey])
		}
	}
	accountedFactoryItems := map[string]struct{}{}
	for position, raw := range m.FactoryItemAccounting {
		var row identityFactoryAccounting
		if err := json.Unmarshal(raw, &row); err != nil {
			return fmt.Errorf("factory_item_accounting[%d] must be an object", position)
		}
		if row.FactoryItemKey == "" || row.Disposition == "" || row.ListingKeys == nil {
			return fmt.Errorf("factory_item_accounting[%d] requires factory_item_key, disposition, and listing_keys", position)
		}
		if _, exists := factoryItems[row.FactoryItemKey]; !exists {
			return fmt.Errorf("factory_item_accounting[%d] references unknown factory_item_key %q", position, row.FactoryItemKey)
		}
		if _, duplicate := accountedFactoryItems[row.FactoryItemKey]; duplicate {
			return fmt.Errorf("duplicate factory_item_accounting row for %q", row.FactoryItemKey)
		}
		accountedFactoryItems[row.FactoryItemKey] = struct{}{}
		kinds, err := validateIdentityEvidence(row.Evidence, fmt.Sprintf("factory_item_accounting[%d]", position), sourceIDs, 1)
		if err != nil {
			return err
		}
		if !kinds["accounting_disposition"] {
			return fmt.Errorf("factory_item_accounting[%d] evidence must include accounting_disposition", position)
		}
		actualListings := factoryItemBoundListings(m.Resolutions, row.FactoryItemKey)
		switch row.Disposition {
		case "mapped":
			if len(row.ListingKeys) == 0 {
				return fmt.Errorf("mapped factory_item_accounting row %q requires listing_keys", row.FactoryItemKey)
			}
			seenListings := map[string]struct{}{}
			for _, listingKey := range row.ListingKeys {
				if _, duplicate := seenListings[listingKey]; duplicate {
					return fmt.Errorf("factory_item_accounting row %q repeats listing %q", row.FactoryItemKey, listingKey)
				}
				seenListings[listingKey] = struct{}{}
				if _, exists := listings[listingKey]; !exists {
					return fmt.Errorf("factory_item_accounting row %q references unknown listing %q", row.FactoryItemKey, listingKey)
				}
				if !resolutionBindsFactoryItem(m.Resolutions, listingKey, row.FactoryItemKey) {
					return fmt.Errorf("factory_item_accounting row %q claims listing %q without a matching resolution binding", row.FactoryItemKey, listingKey)
				}
			}
			if len(seenListings) != len(actualListings) {
				return fmt.Errorf("factory_item_accounting row %q declares %d listings but resolutions bind %d", row.FactoryItemKey, len(seenListings), len(actualListings))
			}
			for listingKey := range actualListings {
				if _, declared := seenListings[listingKey]; !declared {
					return fmt.Errorf("factory_item_accounting row %q omits bound listing %q", row.FactoryItemKey, listingKey)
				}
			}
		case "not_in_price_scraping_scope", "inactive", "non_retail":
			if len(row.ListingKeys) != 0 || strings.TrimSpace(row.Reason) == "" {
				return fmt.Errorf("factory_item_accounting row %q disposition %q requires empty listing_keys and a reason", row.FactoryItemKey, row.Disposition)
			}
			if len(actualListings) != 0 {
				return fmt.Errorf("factory_item_accounting row %q disposition %q contradicts %d resolution bindings", row.FactoryItemKey, row.Disposition, len(actualListings))
			}
		default:
			return fmt.Errorf("factory_item_accounting row %q has unsupported disposition %q", row.FactoryItemKey, row.Disposition)
		}
	}
	if len(accountedFactoryItems) != len(factoryItems) {
		return fmt.Errorf("factory_item_accounting covers %d of %d factory items", len(accountedFactoryItems), len(factoryItems))
	}
	if err := validateIdentityAuxiliaryTables(m, productsByJID, listings, factoryItems, sourceIDs); err != nil {
		return err
	}
	if err := validateResolutionAliasTargets(m.JIDAliases, m.Resolutions); err != nil {
		return err
	}
	if err := validateObservedQueueAccounting(m.ObservedQueueAccounting, sourceIDs); err != nil {
		return err
	}

	if _, err := normalizedCoverage(m.Coverage); err != nil {
		return err
	}
	jidCount := 0
	for _, product := range m.Products {
		if product.JID != "" {
			jidCount++
		}
	}
	activePriceSKUCount := 0
	sourceMappingRowCount := 0
	for _, priceSKU := range m.PriceSKUs {
		if strings.EqualFold(priceSKU.State, "active") {
			activePriceSKUCount++
		}
	}
	for _, listing := range m.Listings {
		sourceMappingRowCount += len(listing.SourceMemberships)
	}
	actualCoverage := map[string]int{
		"price_skus":          len(m.PriceSKUs),
		"active_price_skus":   activePriceSKUCount,
		"source_mapping_rows": sourceMappingRowCount,
		"listings":            len(m.Listings),
		"jids":                jidCount,
		"factory_items":       len(m.FactoryItems),
	}
	declaredCoverage := map[string]*identityCoverageCounter{
		"price_skus":          m.Coverage.PriceSKUs,
		"active_price_skus":   m.Coverage.ActivePriceSKUs,
		"source_mapping_rows": m.Coverage.SourceMappingRows,
		"listings":            m.Coverage.Listings,
		"jids":                m.Coverage.JIDs,
		"factory_items":       m.Coverage.FactoryItems,
	}
	for dimension, actual := range actualCoverage {
		if declaredCoverage[dimension].Expected != actual {
			return fmt.Errorf("coverage.%s.expected=%d but map contains %d", dimension, declaredCoverage[dimension].Expected, actual)
		}
	}
	queueCount, err := identityIssueCount(m.Coverage.QueueEntriesOutsideMaster)
	if err != nil {
		return fmt.Errorf("coverage.queue_entries_outside_current_master: %w", err)
	}
	if queueCount != len(m.ObservedQueueAccounting) {
		return fmt.Errorf("coverage.queue_entries_outside_current_master=%d but map contains %d observed queue accounting rows", queueCount, len(m.ObservedQueueAccounting))
	}
	resolvedActiveListings := map[string]struct{}{}
	for _, resolution := range m.Resolutions {
		if resolution.State == "verified" {
			resolvedActiveListings[resolution.ListingKey] = struct{}{}
		}
	}
	unresolvedActive := 0
	for _, listing := range m.Listings {
		if strings.EqualFold(listing.State, "active") {
			if _, resolved := resolvedActiveListings[listing.ListingKey]; !resolved {
				unresolvedActive++
			}
		}
	}
	declaredUnresolvedActive, err := identityIssueCount(m.Coverage.UnresolvedActiveListings)
	if err != nil {
		return fmt.Errorf("coverage.unresolved_active_listings: %w", err)
	}
	if declaredUnresolvedActive != unresolvedActive {
		return fmt.Errorf("coverage.unresolved_active_listings=%d but map contains %d unresolved active listings", declaredUnresolvedActive, unresolvedActive)
	}
	return nil
}

func validateIdentityAuxiliaryTables(m *productIdentityMap, productsByJID map[string]string, listings map[string]identityListing, factoryItems map[string]identityFactoryItem, sourceIDs map[string]struct{}) error {
	seenAliases := map[string]struct{}{}
	for position, raw := range m.JIDAliases {
		var alias identityJIDAlias
		if err := json.Unmarshal(raw, &alias); err != nil {
			return fmt.Errorf("jid_aliases[%d] must be an object", position)
		}
		if alias.AliasJID == "" || alias.CanonicalJID == "" || alias.Relation == "" || alias.DecisionID == "" || strings.TrimSpace(alias.Reason) == "" {
			return fmt.Errorf("jid_aliases[%d] requires alias_jid, canonical_jid, relation, decision_id, and reason", position)
		}
		if alias.AliasJID == alias.CanonicalJID {
			return fmt.Errorf("jid_aliases[%d] cannot alias a JID to itself", position)
		}
		switch alias.Relation {
		case "duplicate_of", "renamed_to", "merged_into":
		default:
			return fmt.Errorf("jid_aliases[%d] has unsupported relation %q", position, alias.Relation)
		}
		if _, exists := productsByJID[alias.AliasJID]; !exists {
			return fmt.Errorf("jid_aliases[%d] references unknown alias_jid %q", position, alias.AliasJID)
		}
		if _, exists := productsByJID[alias.CanonicalJID]; !exists {
			return fmt.Errorf("jid_aliases[%d] references unknown canonical_jid %q", position, alias.CanonicalJID)
		}
		if _, duplicate := seenAliases[alias.AliasJID]; duplicate {
			return fmt.Errorf("duplicate jid_alias for %q", alias.AliasJID)
		}
		seenAliases[alias.AliasJID] = struct{}{}
		if _, err := validateIdentityEvidence(alias.Evidence, fmt.Sprintf("jid_aliases[%d]", position), sourceIDs, 1); err != nil {
			return err
		}
	}

	seenConflicts := map[string]struct{}{}
	for position, raw := range m.JIDConflicts {
		var conflict identityJIDConflict
		if err := json.Unmarshal(raw, &conflict); err != nil {
			return fmt.Errorf("jid_conflicts[%d] must be an object", position)
		}
		if conflict.ConflictID == "" || conflict.Kind == "" || len(conflict.InvolvedJIDs) < 2 || conflict.InvolvedListingKeys == nil || conflict.Blocking == nil || conflict.ResolutionKind == "" || strings.TrimSpace(conflict.Reason) == "" {
			return fmt.Errorf("jid_conflicts[%d] has incomplete identity, participants, status, or resolution", position)
		}
		switch conflict.Status {
		case "resolved", "resolved_for_price_scope", "open_out_of_price_scope":
		default:
			return fmt.Errorf("jid_conflicts[%d] has unsupported status %q", position, conflict.Status)
		}
		switch conflict.ResolutionKind {
		case "alias", "merge", "split", "keep_distinct", "reassign":
		default:
			return fmt.Errorf("jid_conflicts[%d] has unsupported resolution_kind %q", position, conflict.ResolutionKind)
		}
		if *conflict.Blocking {
			return fmt.Errorf("jid_conflicts[%d] %q is still blocking in a released map", position, conflict.ConflictID)
		}
		if _, duplicate := seenConflicts[conflict.ConflictID]; duplicate {
			return fmt.Errorf("duplicate jid_conflict %q", conflict.ConflictID)
		}
		seenConflicts[conflict.ConflictID] = struct{}{}
		seenJIDs := map[string]struct{}{}
		for _, jid := range conflict.InvolvedJIDs {
			if _, exists := productsByJID[jid]; !exists {
				return fmt.Errorf("jid_conflicts[%d] references unknown jid %q", position, jid)
			}
			if _, duplicate := seenJIDs[jid]; duplicate {
				return fmt.Errorf("jid_conflicts[%d] repeats jid %q", position, jid)
			}
			seenJIDs[jid] = struct{}{}
		}
		seenListings := map[string]struct{}{}
		for _, listingKey := range conflict.InvolvedListingKeys {
			if _, exists := listings[listingKey]; !exists {
				return fmt.Errorf("jid_conflicts[%d] references unknown listing %q", position, listingKey)
			}
			if _, duplicate := seenListings[listingKey]; duplicate {
				return fmt.Errorf("jid_conflicts[%d] repeats listing %q", position, listingKey)
			}
			seenListings[listingKey] = struct{}{}
		}
		if _, err := validateIdentityEvidence(conflict.Evidence, fmt.Sprintf("jid_conflicts[%d]", position), sourceIDs, 1); err != nil {
			return err
		}
	}

	expectedCollisions := map[string]map[string]struct{}{}
	for key, item := range factoryItems {
		if expectedCollisions[item.ItemCode] == nil {
			expectedCollisions[item.ItemCode] = map[string]struct{}{}
		}
		expectedCollisions[item.ItemCode][key] = struct{}{}
	}
	for code, keys := range expectedCollisions {
		if len(keys) < 2 {
			delete(expectedCollisions, code)
		}
	}
	seenCollisions := map[string]struct{}{}
	for position, raw := range m.FactoryCodeCollisions {
		var collision identityFactoryCodeCollision
		if err := json.Unmarshal(raw, &collision); err != nil {
			return fmt.Errorf("factory_code_collisions[%d] must be an object", position)
		}
		if collision.ItemCode == "" || len(collision.FactoryItemKeys) < 2 {
			return fmt.Errorf("factory_code_collisions[%d] requires item_code and at least two factory_item_keys", position)
		}
		switch collision.PhysicalRelation {
		case "same_offer", "different_offer", "mixed":
		default:
			return fmt.Errorf("factory_code_collisions[%d] has unsupported physical_relation %q", position, collision.PhysicalRelation)
		}
		if _, duplicate := seenCollisions[collision.ItemCode]; duplicate {
			return fmt.Errorf("duplicate factory_code_collision for %q", collision.ItemCode)
		}
		seenCollisions[collision.ItemCode] = struct{}{}
		expected, exists := expectedCollisions[collision.ItemCode]
		if !exists {
			return fmt.Errorf("factory_code_collisions[%d] item_code %q is not actually reused", position, collision.ItemCode)
		}
		actual := stringSet(collision.FactoryItemKeys)
		if len(actual) != len(collision.FactoryItemKeys) || len(actual) != len(expected) {
			return fmt.Errorf("factory_code_collisions[%d] does not list each qualified item for %q exactly once", position, collision.ItemCode)
		}
		for key := range expected {
			if _, ok := actual[key]; !ok {
				return fmt.Errorf("factory_code_collisions[%d] omits qualified item %q", position, key)
			}
		}
		if _, err := validateIdentityEvidence(collision.Evidence, fmt.Sprintf("factory_code_collisions[%d]", position), sourceIDs, 1); err != nil {
			return err
		}
	}
	if len(seenCollisions) != len(expectedCollisions) {
		return fmt.Errorf("factory_code_collisions accounts for %d of %d reused bare item codes", len(seenCollisions), len(expectedCollisions))
	}
	return nil
}

func validateResolutionAliasTargets(rawAliases []json.RawMessage, resolutions []identityResolution) error {
	aliases := map[string]string{}
	for _, raw := range rawAliases {
		var alias identityJIDAlias
		if json.Unmarshal(raw, &alias) == nil {
			aliases[alias.AliasJID] = alias.CanonicalJID
		}
	}
	for aliasJID, canonicalJID := range aliases {
		if next, chained := aliases[canonicalJID]; chained {
			return fmt.Errorf("jid alias %q targets alias %q (which targets %q); released maps must flatten alias chains", aliasJID, canonicalJID, next)
		}
	}
	for _, resolution := range resolutions {
		if canonical, aliased := aliases[resolution.CanonicalJID]; aliased {
			return fmt.Errorf("resolution %q targets alias jid %q; canonical jid is %q", resolution.ResolutionID, resolution.CanonicalJID, canonical)
		}
	}
	return nil
}

func validateObservedQueueAccounting(rows []json.RawMessage, sourceIDs map[string]struct{}) error {
	for position, raw := range rows {
		var row identityQueueAccounting
		if err := json.Unmarshal(raw, &row); err != nil {
			return fmt.Errorf("observed_queue_accounting[%d] must be an object", position)
		}
		switch row.SourceSection {
		case "review", "unpriced", "junk":
		default:
			return fmt.Errorf("observed_queue_accounting[%d] has unsupported source_section %q", position, row.SourceSection)
		}
		if row.SourceIndex == nil || *row.SourceIndex < 0 {
			return fmt.Errorf("observed_queue_accounting[%d].source_index must be a non-negative integer", position)
		}
		switch row.EntryKind {
		case "listing_candidate", "family_census", "note":
		default:
			return fmt.Errorf("observed_queue_accounting[%d] has unsupported entry_kind %q", position, row.EntryKind)
		}
		if err := validateNullableIdentityString(row.Platform, fmt.Sprintf("observed_queue_accounting[%d].platform", position)); err != nil {
			return err
		}
		if err := validateNullableIdentityString(row.ListingID, fmt.Sprintf("observed_queue_accounting[%d].listing_id", position)); err != nil {
			return err
		}
		if row.Disposition != "outside_current_price_master" {
			return fmt.Errorf("observed_queue_accounting[%d] has unsupported disposition %q", position, row.Disposition)
		}
		kinds, err := validateIdentityEvidence(row.Evidence, fmt.Sprintf("observed_queue_accounting[%d]", position), sourceIDs, 1)
		if err != nil {
			return err
		}
		if !kinds["accounting_disposition"] {
			return fmt.Errorf("observed_queue_accounting[%d] evidence must include accounting_disposition", position)
		}
	}
	return nil
}

func validateNullableIdentityString(raw json.RawMessage, label string) error {
	if len(raw) == 0 {
		return fmt.Errorf("%s is required", label)
	}
	var value *string
	if err := json.Unmarshal(raw, &value); err != nil {
		return fmt.Errorf("%s must be a string or null", label)
	}
	return nil
}

func validateIdentityPack(raw json.RawMessage, listingKey string) error {
	var pack identityPack
	if len(raw) == 0 || json.Unmarshal(raw, &pack) != nil {
		return fmt.Errorf("listing %q pack must be an object", listingKey)
	}
	switch pack.Kind {
	case "single", "multipack", "bundle", "assortment", "unknown":
	default:
		return fmt.Errorf("listing %q pack has unsupported kind %q", listingKey, pack.Kind)
	}
	if pack.Components == nil {
		return fmt.Errorf("listing %q pack.components is required", listingKey)
	}
	if !validIdentitySHA256(pack.PackFingerprint) {
		return fmt.Errorf("listing %q pack.pack_fingerprint must use sha256:<64 hex>", listingKey)
	}
	return nil
}

func normalizedCoverage(c *identityCoverage) (map[string]any, error) {
	if c == nil {
		return nil, fmt.Errorf("coverage is required")
	}
	counters := map[string]*identityCoverageCounter{
		"price_skus":          c.PriceSKUs,
		"active_price_skus":   c.ActivePriceSKUs,
		"source_mapping_rows": c.SourceMappingRows,
		"listings":            c.Listings,
		"jids":                c.JIDs,
		"factory_items":       c.FactoryItems,
	}
	for name, counter := range counters {
		if counter == nil || counter.Expected <= 0 || counter.Accounted < 0 || counter.Unaccounted < 0 {
			return nil, fmt.Errorf("coverage.%s must contain positive expected and non-negative accounted/unaccounted", name)
		}
		if counter.Accounted != counter.Expected || counter.Unaccounted != 0 {
			return nil, fmt.Errorf("coverage.%s is incomplete: expected=%d accounted=%d unaccounted=%d", name, counter.Expected, counter.Accounted, counter.Unaccounted)
		}
	}
	issues := map[string]json.RawMessage{
		"unresolved_listings":        c.UnresolvedListings,
		"unresolved_active_listings": c.UnresolvedActiveListings,
		"ambiguous_listings":         c.AmbiguousListings,
		"open_jid_conflicts":         c.OpenJIDConflicts,
		"unknown_factory_collisions": c.UnknownFactoryCollisions,
	}
	normalizedIssues := map[string]int{}
	for name, raw := range issues {
		count, err := identityIssueCount(raw)
		if err != nil {
			return nil, fmt.Errorf("coverage.%s: %w", name, err)
		}
		if count != 0 {
			return nil, fmt.Errorf("coverage.%s=%d, want 0", name, count)
		}
		normalizedIssues[name] = count
	}
	if c.SourceIdentitySetsMatch == nil || !*c.SourceIdentitySetsMatch {
		return nil, fmt.Errorf("coverage.source_identity_sets_match must be true")
	}
	queueEntriesOutsideMaster, err := identityIssueCount(c.QueueEntriesOutsideMaster)
	if err != nil {
		return nil, fmt.Errorf("coverage.queue_entries_outside_current_master: %w", err)
	}
	return map[string]any{
		"price_skus":                           counters["price_skus"],
		"active_price_skus":                    counters["active_price_skus"],
		"source_mapping_rows":                  counters["source_mapping_rows"],
		"listings":                             counters["listings"],
		"jids":                                 counters["jids"],
		"factory_items":                        counters["factory_items"],
		"unresolved_listings":                  normalizedIssues["unresolved_listings"],
		"unresolved_active_listings":           normalizedIssues["unresolved_active_listings"],
		"ambiguous_listings":                   normalizedIssues["ambiguous_listings"],
		"open_jid_conflicts":                   normalizedIssues["open_jid_conflicts"],
		"unknown_factory_collisions":           normalizedIssues["unknown_factory_collisions"],
		"source_identity_sets_match":           true,
		"queue_entries_outside_current_master": queueEntriesOutsideMaster,
	}, nil
}

var identityEvidenceKinds = map[string]struct{}{
	"exact_price_code":         {},
	"exact_listing_identity":   {},
	"exact_source_sap":         {},
	"qualified_factory_record": {},
	"review_decision":          {},
	"complete_catalog_absence": {},
	"accounting_disposition":   {},
}

type identityEvidenceClaim struct {
	SourceID      string          `json:"source_id"`
	Pointer       string          `json:"pointer"`
	Claim         string          `json:"claim"`
	EvidenceKind  string          `json:"evidence_kind"`
	ObservedValue json.RawMessage `json:"observed_value,omitempty"`
}

func identitySourceIDs(rawSources []json.RawMessage) (map[string]struct{}, error) {
	ids := map[string]struct{}{}
	for position, raw := range rawSources {
		var source identitySource
		if err := json.Unmarshal(raw, &source); err != nil {
			return nil, fmt.Errorf("sources[%d] must be an object", position)
		}
		if !validIdentitySourceID(source.SourceID) {
			return nil, fmt.Errorf("sources[%d].source_id %q is invalid", position, source.SourceID)
		}
		switch source.Kind {
		case "scrape_catalog", "jid_catalog", "factory_oitm", "review_decisions":
		default:
			return nil, fmt.Errorf("sources[%d] has unsupported kind %q", position, source.Kind)
		}
		if strings.TrimSpace(source.URI) == "" {
			return nil, fmt.Errorf("sources[%d].uri is required", position)
		}
		if _, err := time.Parse(time.RFC3339, source.ObservedAt); err != nil {
			return nil, fmt.Errorf("sources[%d].observed_at must be RFC3339: %w", position, err)
		}
		if !validIdentitySHA256(source.ContentSHA256) || !validIdentitySHA256(source.IdentitySetSHA256) {
			return nil, fmt.Errorf("sources[%d] requires content_sha256 and identity_set_sha256 in sha256:<64 hex> form", position)
		}
		if source.RecordCount == nil || *source.RecordCount < 0 {
			return nil, fmt.Errorf("sources[%d].record_count must be a non-negative integer", position)
		}
		if source.PaginationComplete == nil || !*source.PaginationComplete {
			return nil, fmt.Errorf("sources[%d].pagination_complete must be true", position)
		}
		if source.ReadOnly == nil || !*source.ReadOnly {
			return nil, fmt.Errorf("sources[%d].read_only must be true", position)
		}
		if _, duplicate := ids[source.SourceID]; duplicate {
			return nil, fmt.Errorf("duplicate source_id %q", source.SourceID)
		}
		ids[source.SourceID] = struct{}{}
	}
	return ids, nil
}

func validIdentitySourceID(value string) bool {
	if value == "" {
		return false
	}
	for index, r := range value {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || (index > 0 && (r == '.' || r == '_' || r == '-')) {
			continue
		}
		return false
	}
	return true
}

func validIdentitySHA256(value string) bool {
	if len(value) != len("sha256:")+64 || !strings.HasPrefix(value, "sha256:") {
		return false
	}
	_, err := hex.DecodeString(strings.TrimPrefix(value, "sha256:"))
	return err == nil
}

func validateIdentityEvidence(raw json.RawMessage, label string, sourceIDs map[string]struct{}, minimum int) (map[string]bool, error) {
	var claims []identityEvidenceClaim
	if len(raw) == 0 || json.Unmarshal(raw, &claims) != nil || len(claims) < minimum {
		return nil, fmt.Errorf("%s evidence must be an array with at least %d claim(s)", label, minimum)
	}
	kinds := map[string]bool{}
	for position, claim := range claims {
		if claim.SourceID == "" || claim.Pointer == "" || claim.Claim == "" || claim.EvidenceKind == "" {
			return nil, fmt.Errorf("%s evidence[%d] requires source_id, pointer, claim, and evidence_kind", label, position)
		}
		if _, exists := sourceIDs[claim.SourceID]; !exists {
			return nil, fmt.Errorf("%s evidence[%d] references unknown source_id %q", label, position, claim.SourceID)
		}
		if _, allowed := identityEvidenceKinds[claim.EvidenceKind]; !allowed {
			return nil, fmt.Errorf("%s evidence[%d] has unsupported evidence_kind %q", label, position, claim.EvidenceKind)
		}
		kinds[claim.EvidenceKind] = true
	}
	return kinds, nil
}

func identityFactoryScopeDetails(rawScopes []json.RawMessage) (map[string]identityFactoryScope, error) {
	scopes := map[string]identityFactoryScope{}
	expectedScopes := map[string]struct {
		companyID int
		schema    string
	}{
		"JIVO_OIL":       {companyID: 1, schema: "JIVO_OIL_HANADB"},
		"JIVO_MART":      {companyID: 2, schema: "JIVO_MART_HANADB"},
		"JIVO_BEVERAGES": {companyID: 3, schema: "JIVO_BEVERAGES_HANADB"},
	}
	for _, raw := range rawScopes {
		var scope identityFactoryScope
		if err := json.Unmarshal(raw, &scope); err != nil || scope.FactoryScopeKey == "" || scope.CompanyCode == "" || scope.CompanyID == nil || scope.SAPSchema == "" {
			return nil, fmt.Errorf("every factory_scope requires factory_scope_key, company_code, company_id, and sap_schema")
		}
		expected, exists := expectedScopes[scope.CompanyCode]
		if !exists || expected.companyID != *scope.CompanyID || expected.schema != scope.SAPSchema {
			return nil, fmt.Errorf("factory_scope %q has unsupported company/id/schema tuple", scope.FactoryScopeKey)
		}
		expectedKey := "urn:jivo:factory-scope:" + identityPercentEncode(scope.CompanyCode) + ":" + identityPercentEncode(scope.SAPSchema)
		if scope.FactoryScopeKey != expectedKey {
			return nil, fmt.Errorf("factory_scope key %q disagrees with company/schema; want %q", scope.FactoryScopeKey, expectedKey)
		}
		if _, duplicate := scopes[scope.FactoryScopeKey]; duplicate {
			return nil, fmt.Errorf("duplicate factory_scope_key %q", scope.FactoryScopeKey)
		}
		scopes[scope.FactoryScopeKey] = scope
	}
	return scopes, nil
}

func validateFactoryAbsence(resolutionID string, absence *identityFactoryAbsence, requiredScopes map[string]identityFactoryScope, sourceIDs map[string]struct{}) error {
	if absence == nil {
		return fmt.Errorf("reviewed_absent resolution %q requires factory_absence", resolutionID)
	}
	switch absence.ReasonCode {
	case "not_present_in_complete_factory_catalog", "not_factory_product", "source_gap":
		// Contract values.
	default:
		return fmt.Errorf("reviewed_absent resolution %q has unsupported reason_code %q", resolutionID, absence.ReasonCode)
	}
	if strings.TrimSpace(absence.Reason) == "" || len(absence.Evidence) == 0 {
		return fmt.Errorf("reviewed_absent resolution %q requires a reason and non-empty evidence", resolutionID)
	}
	checked := stringSet(absence.ScopesChecked)
	if len(absence.ScopesChecked) != len(requiredScopes) || len(checked) != len(requiredScopes) {
		return fmt.Errorf("reviewed_absent resolution %q must check all %d Factory scopes", resolutionID, len(requiredScopes))
	}
	for scope := range requiredScopes {
		if _, ok := checked[scope]; !ok {
			return fmt.Errorf("reviewed_absent resolution %q did not check Factory scope %q", resolutionID, scope)
		}
	}
	rawEvidence, err := json.Marshal(absence.Evidence)
	if err != nil {
		return fmt.Errorf("reviewed_absent resolution %q has invalid absence evidence: %w", resolutionID, err)
	}
	kinds, err := validateIdentityEvidence(rawEvidence, "reviewed_absent resolution "+resolutionID, sourceIDs, 2)
	if err != nil {
		return err
	}
	if !kinds["complete_catalog_absence"] || !(kinds["exact_listing_identity"] || kinds["exact_source_sap"] || kinds["exact_price_code"]) {
		return fmt.Errorf("reviewed_absent resolution %q evidence must include an exact listing/source claim and complete_catalog_absence", resolutionID)
	}
	return nil
}

func resolutionBindsFactoryItem(resolutions []identityResolution, listingKey, factoryItemKey string) bool {
	for _, resolution := range resolutions {
		if resolution.ListingKey != listingKey {
			continue
		}
		for _, binding := range resolution.FactoryBindings {
			if binding.FactoryItemKey == factoryItemKey {
				return true
			}
		}
	}
	return false
}

func factoryItemBoundListings(resolutions []identityResolution, factoryItemKey string) map[string]struct{} {
	listings := map[string]struct{}{}
	for _, resolution := range resolutions {
		for _, binding := range resolution.FactoryBindings {
			if binding.FactoryItemKey == factoryItemKey {
				listings[resolution.ListingKey] = struct{}{}
			}
		}
	}
	return listings
}

func identityIssueCount(raw json.RawMessage) (int, error) {
	if len(raw) == 0 || string(raw) == "null" {
		return 0, fmt.Errorf("field is required and must be a non-negative integer")
	}
	var number int
	if err := json.Unmarshal(raw, &number); err == nil {
		if number < 0 {
			return 0, fmt.Errorf("count cannot be negative")
		}
		return number, nil
	}
	return 0, fmt.Errorf("must be a non-negative integer")
}

func (d *identityDataset) envelope(fields map[string]any) map[string]any {
	fields["map_version"] = d.Map.Contract.DatasetVersion
	fields["schema_version"] = d.Map.Contract.SchemaVersion
	fields["map_sha256"] = d.SHA256
	fields["map_path"] = d.Path
	fields["attestation_sha256"] = d.AttestationSHA256
	fields["attestation_path"] = d.AttestationPath
	return fields
}

func (d *identityDataset) actualCounts() map[string]int {
	jidCount := 0
	activePriceSKUCount := 0
	sourceMappingRowCount := 0
	for _, product := range d.Map.Products {
		if product.JID != "" {
			jidCount++
		}
	}
	for _, priceSKU := range d.Map.PriceSKUs {
		if strings.EqualFold(priceSKU.State, "active") {
			activePriceSKUCount++
		}
	}
	for _, listing := range d.Map.Listings {
		sourceMappingRowCount += len(listing.SourceMemberships)
	}
	return map[string]int{
		"products":                             len(d.Map.Products),
		"jids":                                 jidCount,
		"price_skus":                           len(d.Map.PriceSKUs),
		"active_price_skus":                    activePriceSKUCount,
		"source_mapping_rows":                  sourceMappingRowCount,
		"listings":                             len(d.Map.Listings),
		"factory_items":                        len(d.Map.FactoryItems),
		"resolutions":                          len(d.Map.Resolutions),
		"queue_entries_outside_current_master": len(d.Map.ObservedQueueAccounting),
	}
}

func (d *identityDataset) resolveExact(identifier string, flags *rootFlags, allCompanies bool) (string, []identityMatch, error) {
	type anchors struct {
		kind         string
		productKeys  []string
		priceSKUs    []string
		listings     []string
		factoryItems []string
	}
	var candidates []anchors
	aliasProductKey := ""
	for _, rawAlias := range d.Map.JIDAliases {
		alias, canonical := parseJIDAlias(rawAlias)
		if alias != "" && canonical != "" && alias == identifier {
			if product, ok := d.productByJID(canonical); ok {
				aliasProductKey = product.ProductKey
			}
		}
	}
	for _, p := range d.Map.Products {
		if aliasProductKey == "" && p.JID != "" && p.JID == identifier {
			candidates = append(candidates, anchors{kind: "jid", productKeys: []string{p.ProductKey}})
		}
		if p.ProductKey == identifier {
			candidates = append(candidates, anchors{kind: "product_key", productKeys: []string{p.ProductKey}})
		}
	}
	if aliasProductKey != "" {
		candidates = append(candidates, anchors{kind: "jid_alias", productKeys: []string{aliasProductKey}})
	}
	for _, priceSKU := range d.Map.PriceSKUs {
		if priceSKU.PriceSKUKey == identifier {
			candidates = append(candidates, anchors{kind: "price_sku_key", priceSKUs: []string{priceSKU.PriceSKUKey}})
		}
	}
	for _, listing := range d.Map.Listings {
		if listing.ListingKey == identifier {
			candidates = append(candidates, anchors{kind: "listing_key", listings: []string{listing.ListingKey}})
		}
	}
	for _, item := range d.Map.FactoryItems {
		if item.FactoryItemKey == identifier {
			candidates = append(candidates, anchors{kind: "factory_item_key", factoryItems: []string{item.FactoryItemKey}})
		}
	}
	if len(candidates) > 1 {
		return "", nil, usageErr(fmt.Errorf("identifier %q exists in multiple identity namespaces; use the fully qualified listing or Factory key", identifier))
	}
	if len(candidates) == 0 {
		var qualifiedPriceSKUs []string
		for _, priceSKU := range d.Map.PriceSKUs {
			if matchesQualifiedPair(identifier, priceSKU.SourceNamespace, priceSKU.SourceProductCode) {
				qualifiedPriceSKUs = append(qualifiedPriceSKUs, priceSKU.PriceSKUKey)
			}
		}
		if len(qualifiedPriceSKUs) == 1 {
			candidates = append(candidates, anchors{kind: "qualified_price_product_code", priceSKUs: qualifiedPriceSKUs})
		} else if len(qualifiedPriceSKUs) > 1 {
			return "", nil, usageErr(fmt.Errorf("qualified price product code %q is ambiguous; use price_sku_key", identifier))
		}
	}
	if len(candidates) == 0 {
		var sourcePriceSKUs []string
		for _, priceSKU := range d.Map.PriceSKUs {
			if priceSKU.SourceProductCode == identifier {
				sourcePriceSKUs = append(sourcePriceSKUs, priceSKU.PriceSKUKey)
			}
		}
		if len(sourcePriceSKUs) > 0 && (hasBareListingID(d.Map.Listings, identifier) || hasBareFactoryItemCode(d.Map.FactoryItems, identifier)) {
			return "", nil, usageErr(fmt.Errorf("identifier %q is reused across price, listing, or Factory namespaces; use a qualified source/listing/Factory key", identifier))
		}
		if len(sourcePriceSKUs) == 1 {
			candidates = append(candidates, anchors{kind: "price_product_code", priceSKUs: sourcePriceSKUs})
		} else if len(sourcePriceSKUs) > 1 {
			return "", nil, usageErr(fmt.Errorf("price product code %q exists in multiple source namespaces; qualify it as source_namespace:source_product_code", identifier))
		}
	}
	if len(candidates) == 0 {
		var qualifiedListings []string
		for _, listing := range d.Map.Listings {
			if matchesQualifiedPair(identifier, listing.Platform, listing.ListingID) {
				qualifiedListings = append(qualifiedListings, listing.ListingKey)
			}
		}
		if len(qualifiedListings) == 1 {
			candidates = append(candidates, anchors{kind: "qualified_listing", listings: qualifiedListings})
		} else if len(qualifiedListings) > 1 {
			return "", nil, usageErr(fmt.Errorf("qualified listing identifier %q is ambiguous; use listing_key", identifier))
		}
	}
	if len(candidates) == 0 {
		var qualifiedFactoryItems []string
		for _, item := range d.Map.FactoryItems {
			if matchesQualifiedTriple(identifier, item.CompanyCode, item.SAPSchema, item.ItemCode) {
				qualifiedFactoryItems = append(qualifiedFactoryItems, item.FactoryItemKey)
			}
		}
		if len(qualifiedFactoryItems) == 1 {
			candidates = append(candidates, anchors{kind: "qualified_factory_item", factoryItems: qualifiedFactoryItems})
		} else if len(qualifiedFactoryItems) > 1 {
			return "", nil, usageErr(fmt.Errorf("qualified Factory identifier %q is ambiguous; use factory_item_key", identifier))
		}
	}
	if len(candidates) == 0 {
		var listingKeys []string
		for _, listing := range d.Map.Listings {
			if listing.ListingID == identifier {
				listingKeys = append(listingKeys, listing.ListingKey)
			}
		}
		if len(listingKeys) > 0 && hasBareFactoryItemCode(d.Map.FactoryItems, identifier) {
			return "", nil, usageErr(fmt.Errorf("identifier %q is reused as a listing ID and Factory item code; use a qualified listing or Factory key", identifier))
		}
		if len(listingKeys) > 1 {
			sort.Strings(listingKeys)
			return "", nil, usageErr(fmt.Errorf("listing ID %q is reused across platforms; resolve a qualified listing_key instead (%s)", identifier, strings.Join(listingKeys, ", ")))
		}
		if len(listingKeys) == 1 {
			candidates = append(candidates, anchors{kind: "listing_id", listings: listingKeys})
		}
	}
	if len(candidates) == 0 {
		var factoryKeys []string
		for _, item := range d.Map.FactoryItems {
			if item.ItemCode != identifier {
				continue
			}
			if allCompanies || (flags.companyExplicit && item.CompanyCode == flags.companyCode) {
				factoryKeys = append(factoryKeys, item.FactoryItemKey)
			}
		}
		bareExists := false
		for _, item := range d.Map.FactoryItems {
			if item.ItemCode == identifier {
				bareExists = true
				break
			}
		}
		if bareExists && !allCompanies && !flags.companyExplicit {
			return "", nil, usageErr(fmt.Errorf("bare Factory item code %q requires --company (or use --all-companies); JIVO_MART is never assumed for identity", identifier))
		}
		if len(factoryKeys) > 0 {
			candidates = append(candidates, anchors{kind: "factory_item_code", factoryItems: factoryKeys})
		}
	}
	if len(candidates) == 0 {
		return "", nil, notFoundErr(fmt.Errorf("exact product identity %q not found; use 'product search' for text", identifier))
	}
	anchor := candidates[0]
	rows := d.rowsForAnchors(anchor.kind, anchor.productKeys, anchor.priceSKUs, anchor.listings, anchor.factoryItems)
	if flags.companyExplicit && !allCompanies {
		rows = filterIdentityMatchesByCompany(rows, flags.companyCode)
	}
	if len(rows) == 0 {
		return "", nil, notFoundErr(fmt.Errorf("product identity %q has no match in company %s", identifier, flags.companyCode))
	}
	return anchor.kind, rows, nil
}

func (d *identityDataset) rowsForAnchors(kind string, productKeys, priceSKUKeys, listingKeys, factoryItemKeys []string) []identityMatch {
	restrictFactoryBindings := len(factoryItemKeys) > 0 && len(productKeys) == 0 && len(priceSKUKeys) == 0 && len(listingKeys) == 0
	restrictPriceMemberships := len(priceSKUKeys) > 0 && len(productKeys) == 0 && len(listingKeys) == 0 && len(factoryItemKeys) == 0
	listingSet := stringSet(listingKeys)
	factorySet := stringSet(factoryItemKeys)
	productSet := stringSet(productKeys)
	priceSet := stringSet(priceSKUKeys)
	accountingByFactory := d.factoryAccountingIndex()
	collisionByCode := d.factoryCollisionIndex()
	for _, resolution := range d.Map.Resolutions {
		if _, ok := productSet[resolution.CanonicalProductKey]; ok {
			listingSet[resolution.ListingKey] = struct{}{}
		}
	}
	for _, priceSKU := range d.Map.PriceSKUs {
		if _, ok := priceSet[priceSKU.PriceSKUKey]; ok {
			for _, key := range priceSKU.MemberListingKeys {
				listingSet[key] = struct{}{}
			}
		}
	}
	for _, resolution := range d.Map.Resolutions {
		for _, binding := range resolution.FactoryBindings {
			if _, ok := factorySet[binding.FactoryItemKey]; ok {
				listingSet[resolution.ListingKey] = struct{}{}
			}
		}
	}

	var rows []identityMatch
	for listingKey := range listingSet {
		listing, _ := d.listing(listingKey)
		resolution, hasResolution := d.resolution(listingKey)
		product, _ := d.productByKey(resolution.CanonicalProductKey)
		membershipKeys := listing.PriceSKUKeys
		if restrictPriceMemberships {
			membershipKeys = nil
			for _, key := range listing.PriceSKUKeys {
				if _, selected := priceSet[key]; selected {
					membershipKeys = append(membershipKeys, key)
				}
			}
		}
		for _, membershipKey := range membershipKeys {
			priceSKU, _ := d.priceSKU(membershipKey)
			base := identityMatch{
				MatchKind: kind, ProductKey: product.ProductKey, JID: product.JID, CanonicalName: product.CanonicalName, ProductState: product.State,
				PriceSKUKey: priceSKU.PriceSKUKey, SourceNamespace: priceSKU.SourceNamespace, SourceProductCode: priceSKU.SourceProductCode, DisplayName: priceSKU.DisplayName,
				PriceMembershipRole: listingMembershipRole(listing, membershipKey),
				ListingKey:          listing.ListingKey, Platform: listing.Platform, ListingID: listing.ListingID, ListingIDKind: listing.ListingIDKind, ListingTitle: listing.Title, ListingPack: listing.Pack,
				ResolutionID: resolution.ResolutionID, ResolutionState: resolution.State, VerificationMethod: resolution.VerificationMethod, VerifiedBy: resolution.VerifiedBy, VerifiedAt: resolution.VerifiedAt, ResolutionEvidence: resolution.Evidence,
				FactoryMappingState: resolution.FactoryMappingState, FactoryAbsence: resolution.FactoryAbsence,
			}
			if !hasResolution || len(resolution.FactoryBindings) == 0 {
				rows = append(rows, base)
				continue
			}
			for _, binding := range resolution.FactoryBindings {
				if restrictFactoryBindings {
					if _, selected := factorySet[binding.FactoryItemKey]; !selected {
						continue
					}
				}
				item, _ := d.factoryItem(binding.FactoryItemKey)
				row := base
				applyFactoryItem(&row, item, binding.Role)
				applyFactorySafetyMetadata(&row, item, accountingByFactory, collisionByCode)
				row.FactoryBindingEvidence = binding.Evidence
				row.PrimaryForScope = binding.PrimaryForScope
				row.FactoryUOMPerListingOffer = &binding.FactoryUOMPerListingOffer
				row.ConversionState = binding.ConversionState
				rows = append(rows, row)
			}
		}
	}
	if len(listingSet) == 0 {
		for productKey := range productSet {
			product, ok := d.productByKey(productKey)
			if ok {
				rows = append(rows, identityMatch{MatchKind: kind, ProductKey: product.ProductKey, JID: product.JID, CanonicalName: product.CanonicalName, ProductState: product.State})
			}
		}
		for key := range priceSet {
			priceSKU, ok := d.priceSKU(key)
			if ok {
				rows = append(rows, identityMatch{MatchKind: kind, PriceSKUKey: priceSKU.PriceSKUKey, SourceNamespace: priceSKU.SourceNamespace, SourceProductCode: priceSKU.SourceProductCode, DisplayName: priceSKU.DisplayName})
			}
		}
	}
	for factoryKey := range factorySet {
		found := false
		for _, row := range rows {
			if row.FactoryItemKey == factoryKey {
				found = true
				break
			}
		}
		if !found {
			item, ok := d.factoryItem(factoryKey)
			if ok {
				row := identityMatch{MatchKind: kind}
				applyFactoryItem(&row, item, "")
				applyFactorySafetyMetadata(&row, item, accountingByFactory, collisionByCode)
				rows = append(rows, row)
			}
		}
	}
	return dedupeAndSortIdentityMatches(rows)
}

func (d *identityDataset) search(query string, flags *rootFlags) []identityMatch {
	needle := strings.ToLower(strings.TrimSpace(query))
	productSet, priceSet, listingSet, factorySet := map[string]struct{}{}, map[string]struct{}{}, map[string]struct{}{}, map[string]struct{}{}
	for _, product := range d.Map.Products {
		if containsFold(product.CanonicalName, needle) || containsFold(product.JID, needle) || containsFold(product.ProductKey, needle) {
			productSet[product.ProductKey] = struct{}{}
		}
	}
	for _, priceSKU := range d.Map.PriceSKUs {
		if containsFold(priceSKU.DisplayName, needle) || containsFold(priceSKU.SourceProductCode, needle) || containsFold(priceSKU.PriceSKUKey, needle) {
			priceSet[priceSKU.PriceSKUKey] = struct{}{}
		}
	}
	for _, listing := range d.Map.Listings {
		if containsFold(listing.Title, needle) || containsFold(listing.ListingID, needle) || containsFold(listing.ListingKey, needle) || containsFold(listing.Platform, needle) {
			listingSet[listing.ListingKey] = struct{}{}
		}
	}
	for _, item := range d.Map.FactoryItems {
		if containsFold(item.ItemName, needle) || containsFold(item.ItemCode, needle) || containsFold(item.FactoryItemKey, needle) {
			factorySet[item.FactoryItemKey] = struct{}{}
		}
	}
	rows := d.rowsForAnchors("text_search", setKeys(productSet), setKeys(priceSet), setKeys(listingSet), setKeys(factorySet))
	if flags.companyExplicit {
		rows = filterIdentityMatchesByCompany(rows, flags.companyCode)
	}
	return rows
}

func (d *identityDataset) catalog(company string) []identityCatalogEntry {
	accountingByKey := map[string]identityFactoryAccounting{}
	for _, raw := range d.Map.FactoryItemAccounting {
		var row identityFactoryAccounting
		if json.Unmarshal(raw, &row) == nil {
			accountingByKey[row.FactoryItemKey] = row
		}
	}
	var entries []identityCatalogEntry
	for _, item := range d.Map.FactoryItems {
		if item.CompanyCode != company {
			continue
		}
		productSet, jidSet, priceSet, listingSet := map[string]struct{}{}, map[string]struct{}{}, map[string]struct{}{}, map[string]struct{}{}
		for _, resolution := range d.Map.Resolutions {
			bound := false
			for _, binding := range resolution.FactoryBindings {
				if binding.FactoryItemKey == item.FactoryItemKey {
					bound = true
					break
				}
			}
			if !bound {
				continue
			}
			productSet[resolution.CanonicalProductKey] = struct{}{}
			if product, ok := d.productByKey(resolution.CanonicalProductKey); ok && product.JID != "" {
				jidSet[product.JID] = struct{}{}
			}
			listingSet[resolution.ListingKey] = struct{}{}
			if listing, ok := d.listing(resolution.ListingKey); ok {
				for _, priceSKUKey := range listing.PriceSKUKeys {
					priceSet[priceSKUKey] = struct{}{}
				}
			}
		}
		accounting := accountingByKey[item.FactoryItemKey]
		entries = append(entries, identityCatalogEntry{
			CompanyCode: item.CompanyCode, SAPSchema: item.SAPSchema, FactoryItemKey: item.FactoryItemKey,
			FactoryItemCode: item.ItemCode, FactoryItemName: item.ItemName, FactoryItemClass: item.ItemClass, State: item.State,
			Disposition: accounting.Disposition, DispositionReason: accounting.Reason,
			ProductKeys: setKeys(productSet), CanonicalJIDs: setKeys(jidSet), PriceSKUKeys: setKeys(priceSet), ListingKeys: setKeys(listingSet),
		})
	}
	sort.Slice(entries, func(i, j int) bool { return entries[i].FactoryItemKey < entries[j].FactoryItemKey })
	return entries
}

func (d *identityDataset) productByKey(productKey string) (identityProduct, bool) {
	for _, product := range d.Map.Products {
		if product.ProductKey == productKey {
			return product, true
		}
	}
	return identityProduct{}, false
}

func (d *identityDataset) productByJID(jid string) (identityProduct, bool) {
	for _, product := range d.Map.Products {
		if product.JID != "" && product.JID == jid {
			return product, true
		}
	}
	return identityProduct{}, false
}

func (d *identityDataset) priceSKU(key string) (identityPriceSKU, bool) {
	for _, priceSKU := range d.Map.PriceSKUs {
		if priceSKU.PriceSKUKey == key {
			return priceSKU, true
		}
	}
	return identityPriceSKU{}, false
}

func (d *identityDataset) listing(key string) (identityListing, bool) {
	for _, listing := range d.Map.Listings {
		if listing.ListingKey == key {
			return listing, true
		}
	}
	return identityListing{}, false
}

func (d *identityDataset) factoryItem(key string) (identityFactoryItem, bool) {
	for _, item := range d.Map.FactoryItems {
		if item.FactoryItemKey == key {
			return item, true
		}
	}
	return identityFactoryItem{}, false
}

func (d *identityDataset) resolution(listingKey string) (identityResolution, bool) {
	for _, resolution := range d.Map.Resolutions {
		if resolution.ListingKey == listingKey {
			return resolution, true
		}
	}
	return identityResolution{}, false
}

func parseJIDAlias(raw json.RawMessage) (string, string) {
	var obj map[string]any
	if json.Unmarshal(raw, &obj) != nil {
		return "", ""
	}
	firstString := func(keys ...string) string {
		for _, key := range keys {
			if value, ok := obj[key].(string); ok && value != "" {
				return value
			}
		}
		return ""
	}
	return firstString("alias_jid", "alias", "source_jid"), firstString("canonical_jid", "target_jid", "jid")
}

func applyFactoryItem(row *identityMatch, item identityFactoryItem, role string) {
	row.CompanyCode = item.CompanyCode
	row.SAPSchema = item.SAPSchema
	row.FactoryItemKey = item.FactoryItemKey
	row.FactoryItemCode = item.ItemCode
	row.FactoryItemName = item.ItemName
	row.FactoryItemClass = item.ItemClass
	row.BindingRole = role
}

func (d *identityDataset) factoryAccountingIndex() map[string]identityFactoryAccounting {
	index := make(map[string]identityFactoryAccounting, len(d.Map.FactoryItemAccounting))
	for _, raw := range d.Map.FactoryItemAccounting {
		var accounting identityFactoryAccounting
		if json.Unmarshal(raw, &accounting) == nil {
			index[accounting.FactoryItemKey] = accounting
		}
	}
	return index
}

func (d *identityDataset) factoryCollisionIndex() map[string]identityFactoryCodeCollision {
	index := make(map[string]identityFactoryCodeCollision, len(d.Map.FactoryCodeCollisions))
	for _, raw := range d.Map.FactoryCodeCollisions {
		var collision identityFactoryCodeCollision
		if json.Unmarshal(raw, &collision) == nil {
			index[collision.ItemCode] = collision
		}
	}
	return index
}

func applyFactorySafetyMetadata(row *identityMatch, item identityFactoryItem, accountingByFactory map[string]identityFactoryAccounting, collisionByCode map[string]identityFactoryCodeCollision) {
	if accounting, ok := accountingByFactory[item.FactoryItemKey]; ok {
		row.FactoryAccountingDisposition = accounting.Disposition
		row.FactoryAccountingReason = accounting.Reason
	}
	if collision, ok := collisionByCode[item.ItemCode]; ok {
		row.FactoryCollisionRelation = collision.PhysicalRelation
		row.FactoryCollisionEvidence = collision.Evidence
	}
}

func listingMembershipRole(listing identityListing, priceSKUKey string) string {
	for _, membership := range listing.SourceMemberships {
		if membership.PriceSKUKey == priceSKUKey {
			return membership.Role
		}
	}
	return ""
}

func filterIdentityMatchesByCompany(rows []identityMatch, company string) []identityMatch {
	out := make([]identityMatch, 0, len(rows))
	for _, row := range rows {
		if row.CompanyCode == company || row.FactoryMappingState == "reviewed_absent" {
			out = append(out, row)
		}
	}
	return out
}

func dedupeAndSortIdentityMatches(rows []identityMatch) []identityMatch {
	seen := map[string]struct{}{}
	out := make([]identityMatch, 0, len(rows))
	for _, row := range rows {
		key := strings.Join([]string{row.MatchKind, row.ProductKey, row.JID, row.PriceSKUKey, row.ListingKey, row.FactoryItemKey, row.BindingRole}, "\x00")
		if _, exists := seen[key]; exists {
			continue
		}
		seen[key] = struct{}{}
		out = append(out, row)
	}
	sort.Slice(out, func(i, j int) bool {
		left := strings.Join([]string{out[i].ProductKey, out[i].JID, out[i].PriceSKUKey, out[i].ListingKey, out[i].CompanyCode, out[i].SAPSchema, out[i].FactoryItemKey}, "\x00")
		right := strings.Join([]string{out[j].ProductKey, out[j].JID, out[j].PriceSKUKey, out[j].ListingKey, out[j].CompanyCode, out[j].SAPSchema, out[j].FactoryItemKey}, "\x00")
		return left < right
	})
	return out
}

func containsString(values []string, needle string) bool {
	for _, value := range values {
		if value == needle {
			return true
		}
	}
	return false
}

func hasBareListingID(listings []identityListing, identifier string) bool {
	for _, listing := range listings {
		if listing.ListingID == identifier {
			return true
		}
	}
	return false
}

func hasBareFactoryItemCode(items []identityFactoryItem, identifier string) bool {
	for _, item := range items {
		if item.ItemCode == identifier {
			return true
		}
	}
	return false
}

func matchesQualifiedPair(identifier, first, second string) bool {
	for _, separator := range []string{"::", ":", "/", "|"} {
		prefix := first + separator
		if len(identifier) >= len(prefix) && strings.EqualFold(identifier[:len(prefix)], prefix) && identifier[len(prefix):] == second {
			return true
		}
	}
	return false
}

func matchesQualifiedTriple(identifier, first, second, third string) bool {
	for _, separator := range []string{"::", ":", "/", "|"} {
		prefix := strings.Join([]string{first, second}, separator) + separator
		if len(identifier) >= len(prefix) && strings.EqualFold(identifier[:len(prefix)], prefix) && identifier[len(prefix):] == third {
			return true
		}
	}
	return false
}

func identityPercentEncode(value string) string {
	// url.QueryEscape follows RFC 3986 for every character used by identity
	// keys except spaces, which it renders as '+'. The shared map's generator
	// uses percent-encoded spaces, so normalize that one representation.
	return strings.ReplaceAll(url.QueryEscape(value), "+", "%20")
}

func containsFold(value, lowercaseNeedle string) bool {
	return strings.Contains(strings.ToLower(value), lowercaseNeedle)
}

func stringSet(values []string) map[string]struct{} {
	out := make(map[string]struct{}, len(values))
	for _, value := range values {
		out[value] = struct{}{}
	}
	return out
}

func setKeys(values map[string]struct{}) []string {
	out := make([]string, 0, len(values))
	for value := range values {
		out = append(out, value)
	}
	sort.Strings(out)
	return out
}
