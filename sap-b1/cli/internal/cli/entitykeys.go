package cli

import (
	"fmt"
	"net/url"
	"regexp"
	"strings"

	"sapb1/internal/catalog"
	"sapb1/internal/errs"
)

// bareEntitySetRe is what a write command will accept as an entity-set name:
// a bare OData identifier and nothing else. No parentheses, no slash, no query
// string, no dots. That single restriction is what keeps `post` from being a
// generic "POST anything anywhere" tool — see validateWriteEntitySet.
var bareEntitySetRe = regexp.MustCompile(`^[A-Za-z][A-Za-z0-9_]*$`)

// keyedPathRe matches the fully-addressed form an operator may type for `patch`,
// e.g. `Orders(123)` or `BusinessPartners('V10000')`. The inner group is parsed
// and re-encoded — never passed through — so a query string or a trailing
// segment glued onto the end cannot ride along.
var keyedPathRe = regexp.MustCompile(`^([A-Za-z][A-Za-z0-9_]*)\(([^()]*)\)$`)

// validateWriteEntitySet is the gate in front of every write. It insists the
// target is a bare entity set that the embedded catalog knows and that supports
// the given method as a plain entity operation, and it returns the catalog's
// canonical spelling (OData is case-sensitive, operators are not).
//
// The important refusal is the OData ACTION: `Invoices(9)/Cancel`,
// `Drafts(4321)/SaveDraftToDocument`, `Orders(1)/Close`. Those are POSTs too, and
// they are exactly the irreversible operations this tool leaves to a human in the
// SAP client — so the CLI must not be able to express them at all, no matter how
// the argument is spelled.
func validateWriteEntitySet(name, method string) (string, error) {
	trimmed := strings.TrimSpace(name)
	if trimmed == "" {
		return "", &errs.UsageError{Msg: "entity set name is required, e.g. `sapb1 post BusinessPartners`"}
	}

	if !bareEntitySetRe.MatchString(trimmed) {
		return "", &errs.UsageError{Msg: fmt.Sprintf(
			"%q is not a bare entity-set name. Writes address entity sets only (e.g. BusinessPartners, Items) — "+
				"paths with (), /, ?, $ or . are rejected. In particular OData actions like Invoices(9)/Cancel, "+
				"Orders(1)/Close or Drafts(4321)/SaveDraftToDocument are deliberately not supported: posting, "+
				"cancelling and closing documents is left to a human in the SAP B1 client",
			name)}
	}

	svc, ok := catalog.Find(trimmed)
	if !ok {
		suggestions := catalog.Suggest(trimmed, 5)
		msg := fmt.Sprintf("unknown entity set %q — it is not in the Service Layer catalog", name)
		if len(suggestions) > 0 {
			msg += "; did you mean: " + strings.Join(suggestions, ", ")
		}
		return "", &errs.UsageError{Msg: msg}
	}

	if !supportsEntityOperation(svc, method) {
		return "", &errs.UsageError{Msg: fmt.Sprintf(
			"%s does not support %s on the entity itself (the catalog lists: %s) — run `sapb1 ops %s` to see what it does support",
			svc.Service, method, strings.Join(svc.Methods(), ", "), svc.Service)}
	}

	return svc.Service, nil
}

// supportsEntityOperation reports whether the service catalogues method as a
// plain entity operation: POST on the set itself ("Orders") for a create, or
// PATCH on a single entity ("Orders(id)") for an update. Action operations —
// anything with a "/" in the catalogued name — never count.
func supportsEntityOperation(svc catalog.Service, method string) bool {
	for _, op := range svc.Operations {
		if !strings.EqualFold(op.Method, method) {
			continue
		}
		if strings.Contains(op.Name, "/") {
			continue // an action, e.g. Orders(id)/Cancel
		}
		switch strings.ToUpper(method) {
		case "POST":
			if op.Name == svc.Service {
				return true
			}
		case "PATCH":
			if op.Name == svc.Service+"(id)" || op.Name == svc.Service {
				return true
			}
		}
	}
	return false
}

// keyKind is how an entity's key must be rendered in an OData path: numeric keys
// go bare, string keys go inside single quotes.
type keyKind int

const (
	keyUnknown keyKind = iota
	keyNumeric
	keyString
)

// entityKeyKinds records the key type per entity set.
//
// The embedded catalog can't answer this: it records operations as
// "BusinessPartners(id)" with no type for `id`. Guessing from the key's SHAPE is
// what caused the original bug — CardCode "200001" is a perfectly ordinary
// numeric-looking STRING key, and sending BusinessPartners(200001) makes SAP
// reject the request (or, worse, address something else). So the entities you'd
// realistically patch are listed explicitly, and the shape heuristic survives
// only as the fallback for anything not listed.
var entityKeyKinds = map[string]keyKind{
	// Marketing documents and other DocEntry/AbsoluteEntry-keyed objects.
	"Orders":                    keyNumeric,
	"Quotations":                keyNumeric,
	"Invoices":                  keyNumeric,
	"CreditNotes":               keyNumeric,
	"DeliveryNotes":             keyNumeric,
	"Returns":                   keyNumeric,
	"DownPayments":              keyNumeric,
	"PurchaseQuotations":        keyNumeric,
	"PurchaseOrders":            keyNumeric,
	"PurchaseInvoices":          keyNumeric,
	"PurchaseCreditNotes":       keyNumeric,
	"PurchaseDeliveryNotes":     keyNumeric,
	"PurchaseReturns":           keyNumeric,
	"PurchaseDownPayments":      keyNumeric,
	"Drafts":                    keyNumeric,
	"IncomingPayments":          keyNumeric,
	"VendorPayments":            keyNumeric,
	"JournalEntries":            keyNumeric,
	"StockTransfers":            keyNumeric,
	"InventoryGenEntries":       keyNumeric,
	"InventoryGenExits":         keyNumeric,
	"ProductionOrders":          keyNumeric,
	"Activities":                keyNumeric,
	"BusinessPartnerGroups":     keyNumeric,
	"ItemGroups":                keyNumeric,
	"Users":                     keyNumeric,
	"SalesPersons":              keyNumeric,
	"PaymentTermsTypes":         keyNumeric,
	"ShippingTypes":             keyNumeric,
	"BusinessPlaces":            keyNumeric,
	"Employees":                 keyNumeric,
	"EmployeesInfo":             keyNumeric,
	"ServiceCalls":              keyNumeric,
	"Contacts":                  keyNumeric,
	"PurchaseRequests":          keyNumeric,
	"InventoryTransferRequests": keyNumeric,

	// String-keyed master data: CardCode, ItemCode, WarehouseCode, Code, ...
	"BusinessPartners":          keyString,
	"Items":                     keyString,
	"Warehouses":                keyString,
	"ChartOfAccounts":           keyString,
	"Currencies":                keyString,
	"Countries":                 keyString,
	"States":                    keyString,
	"SalesTaxCodes":             keyString,
	"BankPages":                 keyString,
	"ProjectCodes":              keyString,
	"Manufacturers":             keyString,
	"UnitOfMeasurements":        keyString,
	"CustomsGroups":             keyString,
	"BusinessPartnerProperties": keyString,
	"Territories":               keyString,
}

// keyKindFor returns the key kind for entity, or keyUnknown when the entity
// isn't in the table (in which case buildKeyPath falls back to the shape of the
// key itself).
func keyKindFor(entity string) keyKind {
	if k, ok := entityKeyKinds[entity]; ok {
		return k
	}
	return keyUnknown
}

// buildKeyPath builds the OData single-entity path for entity + key, ready for
// the wire: the key is quote-doubled where needed (OData's own escape for a
// literal apostrophe) and then percent-encoded, so what is previewed, what is
// logged and what is requested are the same bytes.
//
// Percent-encoding is not optional here. JIVO item codes contain "/"
// ("OIL/1L/MUS"), which unencoded would add path segments and address something
// else entirely; "#" would truncate the path at a fragment; "%" would produce an
// invalid escape.
func buildKeyPath(entity, key string) (string, error) {
	switch keyKindFor(entity) {
	case keyNumeric:
		if !isAllDigits(key) {
			return "", &errs.UsageError{Msg: fmt.Sprintf(
				"%s is keyed by a number (DocEntry/AbsoluteEntry), but %q isn't one — pass the numeric key, e.g. `--key 123`",
				entity, key)}
		}
		return entity + "(" + key + ")", nil
	case keyString:
		return entity + "('" + escapeKeyLiteral(key) + "')", nil
	default:
		// Not in the table: fall back to the key's shape, which is right for the
		// common cases and no worse than what the operator typed.
		if isAllDigits(key) {
			return entity + "(" + key + ")", nil
		}
		return entity + "('" + escapeKeyLiteral(key) + "')", nil
	}
}

// escapeKeyLiteral doubles embedded apostrophes (OData string escaping) and then
// percent-encodes the result for use in a URL path segment. The apostrophes that
// delimit the literal are re-exposed afterwards, purely so previews and log lines
// stay readable — they are legal unencoded in a path segment.
func escapeKeyLiteral(key string) string {
	doubled := strings.ReplaceAll(key, "'", "''")
	return strings.ReplaceAll(url.PathEscape(doubled), "%27", "'")
}

func isAllDigits(s string) bool {
	if s == "" {
		return false
	}
	for _, r := range s {
		if r < '0' || r > '9' {
			return false
		}
	}
	return true
}

// resolvePatchPath turns the command's argument (plus optional --key) into the
// exact path to PATCH. Both spellings end up going through the same validation
// and the same encoder:
//
//	patch "BusinessPartners('V10000')"      -> parsed, then rebuilt
//	patch BusinessPartners --key V10000     -> built
//
// Nothing is ever passed through verbatim, so `Items('A')?$select=…` and
// `Orders(1)/Cancel` are refusals rather than requests.
func resolvePatchPath(target, key string) (string, error) {
	target = strings.TrimSpace(target)
	if target == "" {
		return "", &errs.UsageError{Msg: "entity is required, e.g. `sapb1 patch \"BusinessPartners('V10000')\"` or `sapb1 patch BusinessPartners --key V10000`"}
	}

	// The inline keyed form: parse out entity + key, then rebuild.
	if m := keyedPathRe.FindStringSubmatch(target); m != nil {
		if strings.TrimSpace(key) != "" {
			return "", &errs.UsageError{Msg: fmt.Sprintf("%q already contains the key, so --key is redundant — drop one of them", target)}
		}
		entity, err := validateWriteEntitySet(m[1], "PATCH")
		if err != nil {
			return "", err
		}
		inner, err := unquoteODataKey(m[2])
		if err != nil {
			return "", err
		}
		return buildKeyPath(entity, inner)
	}

	// Anything else must be a bare entity set plus --key.
	entity, err := validateWriteEntitySet(target, "PATCH")
	if err != nil {
		return "", err
	}
	if strings.TrimSpace(key) == "" {
		return "", &errs.UsageError{Msg: fmt.Sprintf("%q has no key — pass --key <key>, or write it inline as \"%s('<key>')\"", target, entity)}
	}
	return buildKeyPath(entity, key)
}

// unquoteODataKey turns the text between the parentheses back into the raw key:
// `'V10000'` -> V10000 (with ” collapsing to '), `123` -> 123. A quoted literal
// must be properly closed, and a bare one must be a number — anything else is a
// typo worth stopping on rather than forwarding to SAP.
func unquoteODataKey(inner string) (string, error) {
	if inner == "" {
		return "", &errs.UsageError{Msg: "the key inside the parentheses is empty"}
	}
	if strings.HasPrefix(inner, "'") {
		if !strings.HasSuffix(inner, "'") || len(inner) < 2 {
			return "", &errs.UsageError{Msg: fmt.Sprintf("unterminated quoted key %s — write it as Entity('key')", inner)}
		}
		return strings.ReplaceAll(inner[1:len(inner)-1], "''", "'"), nil
	}
	if !isAllDigits(inner) {
		return "", &errs.UsageError{Msg: fmt.Sprintf("key %q is neither a number nor a quoted string — write it as Entity(123) or Entity('ABC')", inner)}
	}
	return inner, nil
}
