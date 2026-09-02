package main

import "strings"

// The read-only guard. It runs BEFORE any socket is opened, and it denies by
// default: a call is legal only if it names a row in the endpoints table, uses
// that row's method, and carries only that row's query/body keys.
//
// Layer ordering matters. The verb scan runs first so that an attempt to reach
// something like /returns/auth/api/gstr1/gendwnldjson fails with "that is a
// generate/download path" rather than the blander "not in the allowlist" — the
// operator needs to know WHY, and a future author needs the test to name it.

// blockedSubstrings are fragments that make a path illegal wherever they appear.
// Each one is a thing RULE 0 forbids on a statutory portal. They are checked
// against the lower-cased path, so no amount of segment trickery hides them.
//
// Note what is NOT here, and why — these were caught by the coverage test:
//   - "file": the portal's own READ paths contain it (efiledReturns,
//     filingsnapshot), so it is handled by the segment scan below.
//   - "/pay" and "/challan": every cash-ledger read lives under
//     payment.gst.gov.in/payment/..., which "/pay" matches. Both are covered by
//     the segment scan instead, where "pay" and "challan" must be a whole
//     segment (so /payment/auth/api/challan/create is still refused, twice
//     over — "challan" and "create").
var blockedSubstrings = []string{
	"logout", "signout", "sign-out", "signin", "sign-in",
	"generate", "download", "dwnld", "upload",
	"setoff", "set-off", "offsetliab",
	"savedraft", "savetodocument", "submit", "freeze",
	"/save", "/create", "/update", "/delete", "/remove", "/edit", "/modify",
	"/reset", "/amend", "/compute", "/proceed", "/cancel",
}

// writeVerbs are tokens that denote a mutation when they are a whole path
// segment (or a whole dash/underscore-separated part of one). Segment-bounded so
// a read like /payment/auth/api/searcharnusngdate is not killed by the "arn"
// inside it, and /returns/auth/api/efiledReturns is not killed by "file".
var writeVerbs = map[string]bool{
	"create": true, "update": true, "delete": true, "remove": true, "edit": true,
	"modify": true, "save": true, "submit": true, "upload": true, "cancel": true,
	"approve": true, "reject": true, "acknowledge": true, "confirm": true,
	"activate": true, "deactivate": true, "pause": true, "resume": true,
	"pay": true, "settle": true, "dispute": true, "generate": true, "gen": true,
	"invite": true, "sync": true, "publish": true, "logout": true, "signout": true,
	"write": true, "file": true, "efile": true, "setoff": true, "offset": true,
	"reset": true, "amend": true, "compute": true, "proceed": true, "freeze": true,
	"challan": true, "download": true, "dwnld": true, "gendwnld": true,
	"offlineutility": true, "revoke": true, "withdraw": true, "opt": true,
}

// forbidden is the guard. name is the allowlist row being invoked; resolved is
// the concrete path after {placeholder} substitution (equal to the template when
// the row has no parameters). query and body are the KEYS the caller intends to
// send — the values never matter to the guard.
func forbidden(method, host, pathTemplate, resolved string, query, body []string) error {
	// 1. Method. GET always; POST only for a row the table marks POST. Nothing
	//    else exists — this binary has no PUT/PATCH/DELETE code path at all.
	m := strings.ToUpper(method)
	if m != methodGET && m != methodPOST {
		return errGuard("HTTP %s is never allowed (this CLI reads; it does not write)", method)
	}

	// 2. Host must be one of the four GST hosts.
	if !knownHost(host) {
		return errGuard("host %q is not a GST portal host", host)
	}

	// 3. Shape of the path itself.
	for _, p := range []string{pathTemplate, resolved} {
		if !strings.HasPrefix(p, "/") || strings.Contains(p, "..") || strings.ContainsAny(p, "?#") {
			return errGuard("path %q is not a plain absolute path", p)
		}
		if err := scanPathForWrites(p); err != nil {
			return err
		}
	}

	// 4. Deny by default: the row must exist, with this method, on this host.
	var ep *Endpoint
	for i := range endpoints {
		if endpoints[i].Path == pathTemplate && endpoints[i].Host == host {
			ep = &endpoints[i]
			break
		}
	}
	if ep == nil {
		return errGuard("%s %s is not in the READ allowlist (deny-by-default; see endpoints.go)", host, pathTemplate)
	}
	if !strings.EqualFold(ep.Method, m) {
		return errGuard("%s is a %s-only endpoint; %s is refused", ep.Name, ep.Method, m)
	}

	// 5. Only the keys the portal itself sends may go on the wire. This is what
	//    stops a helpful future caller adding &action=submit or "flag":"F".
	if bad := notIn(query, ep.Query); bad != "" {
		return errGuard("query parameter %q is not part of %s (allowed: %s)", bad, ep.Name, orNone(ep.Query))
	}
	if bad := notIn(body, ep.Body); bad != "" {
		return errGuard("body key %q is not part of %s (allowed: %s)", bad, ep.Name, orNone(ep.Body))
	}
	return nil
}

// scanPathForWrites applies the two write-detection layers to one path.
func scanPathForWrites(p string) error {
	lp := strings.ToLower(p)
	for _, bad := range blockedSubstrings {
		if strings.Contains(lp, bad) {
			return errGuard("%q contains %q — generate/save/submit/logout-class paths are refused outright", p, bad)
		}
	}
	for _, seg := range strings.Split(lp, "/") {
		for _, part := range strings.FieldsFunc(seg, func(r rune) bool { return r == '-' || r == '_' || r == '.' }) {
			if writeVerbs[part] {
				return errGuard("path segment %q denotes a write; %q is out of scope for a read-only CLI", part, p)
			}
		}
	}
	return nil
}

func knownHost(h string) bool {
	for _, k := range allHosts {
		if k == h {
			return true
		}
	}
	return false
}

// notIn returns the first key of got that is not in allowed ("" if all are).
func notIn(got, allowed []string) string {
	for _, g := range got {
		ok := false
		for _, a := range allowed {
			if g == a {
				ok = true
				break
			}
		}
		if !ok {
			return g
		}
	}
	return ""
}

func orNone(ss []string) string {
	if len(ss) == 0 {
		return "none"
	}
	return strings.Join(ss, ", ")
}
