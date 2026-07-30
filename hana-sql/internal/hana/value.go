package hana

import (
	"database/sql"
	"fmt"
	"math/big"
	"reflect"
	"strconv"
	"strings"
	"time"

	"github.com/SAP/go-hdb/driver"
)

// Column is one result column: its name and the HANA type name, so a caller can
// tell DECIMAL (exact, returned as a string) from DOUBLE (a JSON number).
type Column struct {
	Name string `json:"name"`
	Type string `json:"type"`
}

// colPlan is how one column is scanned and rendered.
//
// Everything is scanned into *any except LOBs. Scanning a HANA LOB into an
// `any` is the classic trap: the driver hands back an internal lob-locator
// object, and fmt-ing it prints "typecode ltcUndefined ... bytes [83 69 ...]"
// instead of the text (verified against SYS.VIEWS.DEFINITION with the old CLI).
// LOB columns therefore get a pre-declared driver.NullLob whose writer is a
// capped buffer.
type colPlan struct {
	col      Column
	scale    int
	hasScale bool

	isLob bool
	lob   *driver.NullLob
	buf   *capWriter

	val *any
}

func (p *colPlan) dest() any {
	if p.isLob {
		return p.lob
	}
	return p.val
}

func (p *colPlan) reset() {
	if p.isLob {
		p.buf.reset()
		p.lob.Valid = false
	}
}

func (p *colPlan) render() any {
	if p.isLob {
		if !p.lob.Valid {
			return nil
		}
		s := string(p.buf.buf)
		if p.buf.clipped {
			s += lobClipMarker
		}
		return s
	}
	return normalize(*p.val, p.col.Type, p.scale, p.hasScale)
}

const lobClipMarker = " …[clipped]"

// newColPlans builds the per-column scan plan from the driver's column
// metadata.
//
// Duplicate column names are made unique (X, X_2, X_3). Rows are JSON objects,
// so two columns called X would otherwise collapse into one key and silently
// drop a value — the kind of quiet wrong answer this whole tool exists to
// avoid. An unnamed column (SELECT 1 FROM DUMMY on some builds) becomes COL_n.
//
// The generated name is checked against every name already assigned AND against
// every name a real column claims: `SELECT 1 AS X, 2 AS X, 3 AS X_2` used to
// produce columns [X, X_2, X_2] and a row with only two keys, dropping the value
// 2 and leaving the advertised `columns` array disagreeing with the row — the
// exact silent data loss this function exists to prevent.
//
// Two rules, in this order:
//
//  1. a column KEEPS the name the driver gave it whenever that name is still
//     free, so `AS X_2` comes back as X_2 and not as something invented;
//  2. a generated disambiguator may never take a name that some other real
//     column claims, so it keeps incrementing (X_2, X_3, …) past them.
//
// `SELECT 1 AS X, 2 AS X, 3 AS X_2` therefore yields [X, X_3, X_2].
func newColPlans(names []string, cts []*sql.ColumnType, lobLimit int) []*colPlan {
	plans := make([]*colPlan, len(names))
	// Every name the driver actually reported, so a generated name cannot steal
	// one that belongs to a real column further down the list.
	claimed := make(map[string]int, len(names))
	for _, n := range names {
		if n != "" {
			claimed[n]++
		}
	}
	used := make(map[string]bool, len(names))
	// free reports whether cand may be assigned to the column whose driver-given
	// name is orig. A column may always keep its own name; it may take another
	// name only if no real column claims it.
	free := func(cand, orig string) bool {
		return !used[cand] && (cand == orig || claimed[cand] == 0)
	}
	for i, orig := range names {
		name := orig
		if name == "" {
			name = fmt.Sprintf("COL_%d", i+1)
		}
		if !free(name, orig) {
			base := name
			for n := 2; ; n++ {
				cand := fmt.Sprintf("%s_%d", base, n)
				if free(cand, orig) {
					name = cand
					break
				}
			}
		}
		used[name] = true
		p := &colPlan{col: Column{Name: name, Type: "UNKNOWN"}}
		if i < len(cts) && cts[i] != nil {
			ct := cts[i]
			if n := ct.DatabaseTypeName(); n != "" {
				p.col.Type = sqlTypeName(n)
			}
			if _, scale, ok := ct.DecimalSize(); ok {
				p.scale, p.hasScale = int(scale), true
			}
			p.isLob = isLobColumn(ct.ScanType(), p.col.Type)
		}
		if p.isLob {
			p.buf = &capWriter{limit: lobLimit}
			p.lob = &driver.NullLob{Lob: driver.NewLob(nil, p.buf)}
		} else {
			p.val = new(any)
		}
		plans[i] = p
	}
	return plans
}

// sqlTypeName turns HANA's INTERNAL column type name into the SQL type name a
// caller can actually use.
//
// go-hdb reports the storage type, not the declared type: OINV."DocDate" is
// declared TIMESTAMP but comes back as LONGDATE, TO_DATE() comes back as
// DAYDATE, and every DECIMAL(p,s) comes back as FIXED8/FIXED12/FIXED16
// (verified live 2026-07-30 against SYS.TABLE_COLUMNS, which reports TIMESTAMP
// and DECIMAL for the same columns). Callers are told to use columns[].type to
// tell an exact DECIMAL from a float DOUBLE, so reporting FIXED12 breaks the one
// promise the field exists to keep.
func sqlTypeName(dbType string) string {
	switch strings.ToUpper(dbType) {
	case "DAYDATE":
		return "DATE"
	case "SECONDTIME":
		return "TIME"
	case "LONGDATE":
		return "TIMESTAMP"
	case "FIXED8", "FIXED12", "FIXED16":
		return "DECIMAL"
	}
	return dbType
}

// isLobColumn reports whether a column must be scanned through a Lob target.
// Checked two ways (driver scan type and HANA type name) so neither a driver
// change nor an unusual type name can silently reintroduce the raw-locator bug.
func isLobColumn(scanType reflect.Type, dbType string) bool {
	for scanType != nil && scanType.Kind() == reflect.Pointer {
		scanType = scanType.Elem()
	}
	if scanType != nil {
		switch scanType.Name() {
		case "Lob", "NullLob":
			return true
		}
	}
	switch strings.ToUpper(dbType) {
	case "CLOB", "NCLOB", "BLOB", "TEXT", "BINTEXT":
		return true
	}
	return false
}

// normalize turns one driver value into something JSON can carry losslessly.
//
//	DECIMAL   -> exact decimal STRING (never a big.Rat fraction such as
//	             "1517229522682600/1000", never a silently rounded float)
//	DATE      -> "2006-01-02"          (not an RFC3339 midnight)
//	TIME      -> "15:04:05"
//	TIMESTAMP -> "2006-01-02T15:04:05.999999999" with NO zone suffix, except at
//	             exactly midnight, which is a business date (see timeString)
//	[]byte    -> string
//	NULL      -> nil
func normalize(v any, dbType string, scale int, hasScale bool) any {
	switch t := v.(type) {
	case nil:
		return nil
	case *big.Rat:
		return ratString(t, scale, hasScale)
	case big.Rat:
		return ratString(&t, scale, hasScale)
	case *driver.Decimal:
		return ratString((*big.Rat)(t), scale, hasScale)
	case []byte:
		return string(t)
	case time.Time:
		return timeString(t, dbType)
	default:
		return v
	}
}

// ratString renders a HANA DECIMAL exactly.
//
// It prefers the column's declared scale (so OCRD."Balance", DECIMAL(_,6),
// prints as "1074316124.550000" — matching what TO_VARCHAR would give) but only
// when that is lossless; otherwise it walks up to the shortest scale that
// round-trips exactly. A crore figure is never quietly rounded.
func ratString(r *big.Rat, scale int, hasScale bool) string {
	if r == nil {
		return ""
	}
	if hasScale && scale >= 0 && scale <= maxDecimalScale {
		if s := r.FloatString(scale); ratExact(s, r) {
			return s
		}
	}
	for n := 0; n <= maxDecimalScale; n++ {
		if s := r.FloatString(n); ratExact(s, r) {
			return s
		}
	}
	return r.FloatString(maxDecimalScale)
}

const maxDecimalScale = 40

func ratExact(s string, r *big.Rat) bool {
	var q big.Rat
	if _, ok := q.SetString(s); !ok {
		return false
	}
	return q.Cmp(r) == 0
}

// timeString renders a temporal value.
//
// The midnight rule is not cosmetic, it is a correctness fix measured against
// the live database: SAP Business One does NOT use HANA's DATE type. Every
// business date — OINV."DocDate", OINV."DocDueDate", OJDT."RefDate" — is
// declared TIMESTAMP and carries a zero clock (verified 2026-07-30:
// SYS.TABLE_COLUMNS reports DATA_TYPE_NAME = TIMESTAMP for all of them, and
// OINV."DocDate" for DocEntry 77449 came back as 2026-07-30 00:00:00). Rendering
// those as an RFC3339 midnight ("2026-07-30T00:00:00Z") invites a reader — human
// or model — to treat a posting date as an instant with a timezone.
//
// So a TIMESTAMP whose clock is exactly 00:00:00.000000000 is rendered as a bare
// date. A genuine timestamp that lands precisely on midnight loses the "T00:00:00"
// suffix; columns[].type still says TIMESTAMP, so that remains visible, and no
// SAP B1 date column is affected by the ambiguity because none of them ever
// carries a clock.
//
// The non-midnight branch has the same honesty problem in a subtler form, and it
// is fixed the same way: a HANA TIMESTAMP carries NO time zone. It is a wall
// clock, and on this server that wall clock is IST. Formatting it with
// RFC3339Nano stamped a "Z" on it and turned the server's local time into a UTC
// claim that is 5h30m wrong — measured live 2026-07-30:
//
//	SELECT CURRENT_TIMESTAMP, CURRENT_UTCTIMESTAMP FROM DUMMY
//	  -> 2026-07-30 19:33:19.913   (local wall clock, what CURRENT_TIMESTAMP is)
//	  -> 2026-07-30 14:03:19.913   (the actual UTC instant)
//
// So a timestamp with a clock is rendered WITHOUT any zone suffix. That is the
// truthful shape for a zone-less value: it says "this is the wall clock the
// database recorded" and refuses to imply an instant it does not know.
const timestampLayout = "2006-01-02T15:04:05.999999999"

func timeString(t time.Time, dbType string) string {
	switch strings.ToUpper(dbType) {
	case "DATE", "DAYDATE":
		return t.Format("2006-01-02")
	case "TIME", "SECONDTIME":
		return t.Format("15:04:05")
	default:
		if isMidnight(t) {
			return t.Format("2006-01-02")
		}
		// The fractional part uses ".999999999", which omits trailing zeros, so a
		// whole-second value reads "2026-07-30T09:15:00" while HANA's sub-second
		// digits (up to 7) survive when they are there.
		return t.Format(timestampLayout)
	}
}

func isMidnight(t time.Time) bool {
	h, m, s := t.Clock()
	return h == 0 && m == 0 && s == 0 && t.Nanosecond() == 0
}

// capWriter is the LOB sink: it keeps at most limit bytes and records that it
// clipped. It always reports a full write so the driver never sees a short
// write. Note the server still streams the whole LOB — the cap bounds memory
// and the model's context, not the transfer.
type capWriter struct {
	buf     []byte
	limit   int
	clipped bool
}

func (w *capWriter) reset() {
	w.buf = w.buf[:0]
	w.clipped = false
}

func (w *capWriter) Write(p []byte) (int, error) {
	if w.limit <= 0 {
		w.buf = append(w.buf, p...)
		return len(p), nil
	}
	room := w.limit - len(w.buf)
	if room <= 0 {
		w.clipped = true
		return len(p), nil
	}
	if len(p) > room {
		w.buf = append(w.buf, p[:room]...)
		w.clipped = true
		return len(p), nil
	}
	w.buf = append(w.buf, p...)
	return len(p), nil
}

// CellText renders a normalized value for the plain-text CLI (TSV/CSV), where
// SQL NULL has always printed as the literal NULL.
//
// Floats get 'f' formatting, never 'e'. HANA returns DOUBLE for the standard
// money recipe ROUND(TO_DOUBLE(SUM(...)), 2), and Go's default %v prints that as
// 1.07431612455e+09 — a receivables figure an Accounts user cannot read and a
// script cannot parse. 'f' with precision -1 keeps the shortest representation
// that round-trips exactly, so no digit is invented and none is lost.
func CellText(v any) string {
	if v == nil {
		return "NULL"
	}
	switch t := v.(type) {
	case string:
		return t
	case float64:
		return strconv.FormatFloat(t, 'f', -1, 64)
	case float32:
		return strconv.FormatFloat(float64(t), 'f', -1, 32)
	}
	return fmt.Sprintf("%v", v)
}

// approxSize estimates a value's JSON footprint, for the response byte cap.
func approxSize(v any) int {
	switch t := v.(type) {
	case nil:
		return 4
	case string:
		return len(t) + 2
	case bool:
		return 5
	default:
		return 12
	}
}
