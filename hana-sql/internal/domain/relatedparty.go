package domain

import (
	"fmt"
	"regexp"
	"sort"
	"strings"
)

// --- who counts as "not an outside sale" ----------------------------------------
//
// Correction C-0002 says JIVO Mart (CardCode 'CUSTA000606') is Oil's biggest
// customer and that Oil + Mart gross double-counts the stock transfer. Its
// EVIDENCE section says more than its one-line rule does:
//
//	"Mart's books also carry JIVO MART branch cards (DL/PB/HR/KT/KR/RJ/UP) and a
//	 JIVO WELLNESS PVT LTD card needing the same treatment."
//
// This package used to split on 'CUSTA000606' ALONE, which meant every one of
// those branch cards was reported as an EXTERNAL sale. Measured live 2026-08-01
// for April–July 2026, that mislabelled:
//
//	Mart  CUSTA000874  JIVO MART PVT LTD - DL   Rs  9.58 Cr
//	Mart  CUSTA000001  JIVO WELLNESS PVT LTD    Rs  1.94 Cr
//	Mart  CUSTA000827  JIVO MART PVT LTD - HR   Rs  1.65 Cr
//	Oil   CUSTA000002  JIVO WELLNESS PVT LTD-HR Rs  0.62 Cr
//	Oil   CUSTA000001  JIVO WELLNESS PVT LTD-DL Rs  0.30 Cr
//	Oil   CUSTA000003  JIVO WELLNESS PVT LTD-PB Rs  0.07 Cr
//
// It reached the flagship figure: Mart's June-2026 OLIVE "EXTERNAL" of
// Rs 11,99,84,544.83 contained Rs 1,52,91,011.60 (12.7%) billed to Mart's own
// Delhi branch. Splitting on one card code did not encode C-0002; it encoded a
// third of it.
//
// WHY A CATALOGUE OF CODES AND NOT A NAME MATCH. Correction C-0003 forbids
// classifying by matching names, and it is right: a name pattern is a guess that
// silently changes meaning when someone edits a master record. The split is
// therefore keyed on exact CardCodes, verified against OCRD. The name pattern
// appears exactly once in this package, as a DRIFT ALARM (see
// UnlistedRelatedPartyExpr) that can only ever add a warning — never move money
// between buckets.
//
// CARD CODES ARE SCHEMA-LOCAL. 'CUSTA000001' is JIVO WELLNESS in all three
// books but 'CUSTA000827' is JIVO MART - HR in Mart's and JIVO MART PRIVATE
// LIMITED (HARYANA) in Oil's, and Mart's own books have no 'CUSTA000606' at all.
// So the catalogue is keyed by SCHEMA, and the codes for one company are never
// applied to another.

// RelatedParty is one JIVO-group customer card in one company's books: a sister
// company or a branch of the same legal entity. Money billed to it is an
// internal transfer, not an outside sale.
type RelatedParty struct {
	CardCode string `json:"card_code"`
	CardName string `json:"card_name"`
}

// relatedPartyCards is the catalogue, keyed by schema.
//
// VERIFIED LIVE 2026-08-01 against each schema's OCRD, restricted to customer
// cards ("CardType" = 'C'); supplier cards are not on the sales side and are not
// listed. TestLiveRelatedPartyCatalogueMatchesOCRD re-derives this set from the
// database and fails when SAP and this list disagree, so a new branch card
// cannot sit in EXTERNAL unnoticed the way CUSTA000874 did.
var relatedPartyCards = map[string][]RelatedParty{
	"JIVO_OIL_HANADB": {
		{"CUSTA000001", "JIVO WELLNESS PVT LTD - DL"},
		{"CUSTA000002", "JIVO WELLNESS PVT LTD - HR"},
		{"CUSTA000003", "JIVO WELLNESS PVT LTD - PB"},
		{"CUSTA000004", "JIVO WELLNESS PVT LTD- HP"},
		{"CUSTA000606", "JIVO MART PVT LTD"},
		{"CUSTA000827", "JIVO MART PRIVATE LIMITED ( HARYANA )"},
		{"CUSTA000906", "JIVO BEVERAGES-CUST"},
		{"CUSTA001099", "JIVO WELLNESS PVT LTD - DL ISD"},
		{"CUSTA001113", "JIVO MART PVT LTD - SERVICE"},
	},
	"JIVO_MART_HANADB": {
		{"CUSTA000001", "JIVO WELLNESS PVT LTD"},
		{"CUSTA000827", "JIVO MART PVT LTD - HR"},
		{"CUSTA000874", "JIVO MART PVT LTD - DL"},
		{"CUSTA000875", "JIVO MART PVT LTD - PB"},
		{"CUSTA000876", "JIVO MART PVT LTD - KR"},
		{"CUSTA000877", "JIVO MART PVT LTD - RJ"},
		{"CUSTA000878", "JIVO MART PVT LTD - UP"},
		{"CUSTA000926", "JIVO MART PVT LTD -ISD- DL"},
	},
	"JIVO_BEVERAGES_HANADB": {
		{"CUSTA000001", "JIVO WELLNESS PVT LTD - DL"},
		{"CUSTA000002", "JIVO WELLNESS PVT LTD - HR"},
		{"CUSTA000003", "JIVO WELLNESS PVT LTD - PB"},
		{"CUSTA000004", "JIVO WELLNESS PVT LTD- HP"},
		{"CUSTA000606", "JIVO MART PVT LTD"},
		{"CUSTA000827", "JIVO MART PRIVATE LIMITED ( HARYANA )"},
	},
}

// cardCodePattern is what a CardCode is allowed to look like.
//
// The codes below are interpolated into an IN list rather than bound, because
// the list length varies per schema and the values are a compile-time constant,
// exactly like the schema names. That is only safe while no code can carry a
// quote, so the shape is asserted — by TestRelatedPartyCardCodesAreInert at
// build time, and here at the point of use.
var cardCodePattern = regexp.MustCompile(`^[A-Z]{2,8}[0-9]{4,10}$`)

// RelatedPartyCards returns one schema's related-party customer cards.
// The result is a copy: a caller cannot edit the catalogue through it.
func RelatedPartyCards(schema string) []RelatedParty {
	src := relatedPartyCards[schema]
	out := make([]RelatedParty, len(src))
	copy(out, src)
	sort.Slice(out, func(i, j int) bool { return out[i].CardCode < out[j].CardCode })
	return out
}

// relatedPartyList renders one schema's codes as a SQL IN list.
//
// It PANICS on a code that is not inert. A malformed catalogue entry is a
// programming error caught by the package's own tests long before deployment,
// and the alternative — quietly dropping the code — would put a related party
// back into EXTERNAL, which is the bug this file exists to fix.
func relatedPartyList(schema string) string {
	cards := RelatedPartyCards(schema)
	if len(cards) == 0 {
		// No catalogue for this schema: '' can never equal a real CardCode, so the
		// internal bucket is empty and EXTERNAL is gross. The drift alarm still
		// fires, so the answer says so rather than implying there is nothing to
		// classify.
		return "''"
	}
	parts := make([]string, 0, len(cards))
	for _, c := range cards {
		if !cardCodePattern.MatchString(c.CardCode) {
			panic(fmt.Sprintf("domain: related-party CardCode %q for schema %q is not of the inert form LETTERS+DIGITS; it must never be interpolated into SQL", c.CardCode, schema))
		}
		parts = append(parts, "'"+c.CardCode+"'")
	}
	return strings.Join(parts, ", ")
}

// internalCaseExpr is the CASE predicate that puts a line in the INTERNAL bucket.
// externalCaseExpr is its exact complement, so EXTERNAL + INTERNAL = GROSS holds
// for every row including one with a NULL "CardCode" (cardCodeExpr COALESCEs).
func internalCaseExpr(schema string) string {
	return fmt.Sprintf("%s IN (%s)", cardCodeExpr, relatedPartyList(schema))
}

func externalCaseExpr(schema string) string {
	return fmt.Sprintf("%s NOT IN (%s)", cardCodeExpr, relatedPartyList(schema))
}

// JivoNamePattern is the drift alarm's pattern, and the ONLY name match in this
// package.
//
// It never classifies. It answers one question: "is there money sitting in
// EXTERNAL that was billed to a card whose master record calls it JIVO?" A
// non-zero UNLISTED_JIVO_CARD_NET means SAP has a JIVO-named customer card this
// catalogue has not been told about — the CUSTA000874 failure, live, while it is
// happening — so the answer can say EXTERNAL is an upper bound instead of
// presenting it as final. C-0003 forbids name matching as a CLASSIFIER; a
// tripwire that can only add a warning is the opposite of the defect it targets.
const JivoNamePattern = "%JIVO%"

// UnlistedRelatedPartyExpr is the drift-alarm predicate: a JIVO-named card that
// is NOT in the catalogue. bpAlias is the OCRD alias joined on the CardCode.
func UnlistedRelatedPartyExpr(schema, bpAlias string) string {
	return fmt.Sprintf("UPPER(COALESCE(%s.\"CardName\", '')) LIKE '%s' AND %s NOT IN (%s)",
		bpAlias, JivoNamePattern, cardCodeExpr, relatedPartyList(schema))
}

// relatedPartySentence names, in plain text, the cards a company's INTERNAL
// column is made of, so the split is auditable from the answer alone.
func relatedPartySentence(schema string) string {
	cards := RelatedPartyCards(schema)
	if len(cards) == 0 {
		return "no related-party cards are catalogued for this company, so INTERNAL_RELATED_PARTY is 0.00 and EXTERNAL_NET equals GROSS"
	}
	parts := make([]string, 0, len(cards))
	for _, c := range cards {
		parts = append(parts, fmt.Sprintf("%s (%s)", c.CardCode, c.CardName))
	}
	return "INTERNAL_RELATED_PARTY is the sum over these JIVO-group cards in this company's books: " + strings.Join(parts, "; ")
}
