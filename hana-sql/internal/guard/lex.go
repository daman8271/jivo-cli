package guard

import (
	"fmt"
	"strings"
)

// Masked is the result of lexing one SQL statement into a form that is safe to
// pattern-match against.
//
// Text is the statement with every literal replaced by a placeholder:
//
//	single-quoted string       'anything at all'   -> '?'
//	double-quoted identifier   "DocTotal"          -> "I"
//	line comment               -- to end of line   -> one space
//	block comment              /* ... */           -> one space
//
// Tokens is the upper-cased list of word-runs found in Text, in order. Because
// literals are already masked, a keyword that appears inside a string or as a
// quoted identifier can never show up as a token — which is exactly why
//
//	SELECT 'DROP TABLE X' FROM DUMMY
//	SELECT "UPDATE" FROM T
//
// are allowed while a real DROP or UPDATE is not.
type Masked struct {
	Text   string
	Tokens []string
	// QuotedIdents holds the upper-cased CONTENT of every double-quoted
	// identifier, which Text has already replaced with maskIdent. Masking is
	// what lets `SELECT 'drop table x'` and a column literally named "UPDATE"
	// through, but it also hides a quoted keyword from the layer-3 token scan.
	// Layer 3 re-inspects this list for the few names that are dangerous even
	// when delimited — see dangerousQuoted in guard.go.
	QuotedIdents []string
}

const (
	maskString = "'?'"
	maskIdent  = `"I"`
)

// Normalize lexes stmt in a single pass and returns its masked form.
//
// It fails closed. Anything that would make the remainder of the statement
// invisible to the later layers — an unterminated string, an unterminated
// quoted identifier, an unterminated block comment — is a refusal rather than a
// best-effort guess. So is any non-ASCII or control character outside a
// literal, because look-alike (homoglyph) and zero-width characters are a way
// to smuggle a verb past a first-token check.
func Normalize(stmt string) (Masked, error) {
	src := []rune(stmt)
	var out strings.Builder
	out.Grow(len(stmt))
	var quoted []string

	for i := 0; i < len(src); {
		c := src[i]
		switch {
		case c == '\'':
			j, err := scanQuoted(src, i, '\'')
			if err != nil {
				return Masked{}, err
			}
			out.WriteString(maskString)
			i = j

		case c == '"':
			j, err := scanQuoted(src, i, '"')
			if err != nil {
				return Masked{}, err
			}
			// src[i] is the opening quote and src[j-1] the closing one; the
			// content between them is what a later layer needs to see.
			quoted = append(quoted, strings.ToUpper(string(src[i+1:j-1])))
			out.WriteString(maskIdent)
			i = j

		case c == '-' && i+1 < len(src) && src[i+1] == '-':
			j := i + 2
			for j < len(src) && src[j] != '\n' {
				j++
			}
			out.WriteByte(' ')
			i = j

		case c == '/' && i+1 < len(src) && src[i+1] == '*':
			j, err := scanBlockComment(src, i)
			if err != nil {
				return Masked{}, err
			}
			out.WriteByte(' ')
			i = j

		case c > 127:
			return Masked{}, &Refusal{Layer: 0, Msg: fmt.Sprintf(
				"non-ASCII character %q outside a quoted literal — refusing, because look-alike (homoglyph) and zero-width characters can disguise a keyword; put non-ASCII text inside quotes", c)}

		case c < 0x20 && c != '\t' && c != '\n' && c != '\r':
			return Masked{}, &Refusal{Layer: 0, Msg: fmt.Sprintf(
				"control character %q outside a quoted literal", c)}

		default:
			out.WriteRune(c)
			i++
		}
	}

	text := out.String()
	return Masked{Text: text, Tokens: tokenize(text), QuotedIdents: quoted}, nil
}

// scanQuoted consumes a quoted run starting at the opening quote src[start] and
// returns the index just past the closing quote. A doubled quote (two single or
// two double quotes) is an escaped quote inside the run, not the end of it.
func scanQuoted(src []rune, start int, q rune) (int, error) {
	for i := start + 1; i < len(src); i++ {
		if src[i] != q {
			continue
		}
		if i+1 < len(src) && src[i+1] == q { // '' or "" escape
			i++
			continue
		}
		return i + 1, nil
	}
	what := "string literal (')"
	if q == '"' {
		what = `quoted identifier (")`
	}
	return 0, &Refusal{Layer: 0, Msg: "unterminated " + what +
		" — refusing, because an unclosed quote hides the rest of the statement from the read-only check"}
}

// scanBlockComment consumes /* ... */ starting at src[start] and returns the
// index just past the closing */. HANA block comments do not nest.
func scanBlockComment(src []rune, start int) (int, error) {
	for j := start + 2; j+1 < len(src); j++ {
		if src[j] == '*' && src[j+1] == '/' {
			return j + 2, nil
		}
	}
	return 0, &Refusal{Layer: 0, Msg: "unterminated block comment (/* … */)" +
		" — refusing, because an unclosed comment hides the rest of the statement from the read-only check"}
}

// isWordRune reports whether c can appear inside a SQL word token.
//
// '#', '$' and '@' count as word characters on purpose: HANA identifiers may
// contain them, and treating them as separators would split a harmless name
// like MY$UPDATE into a false "UPDATE" hit. They can never create a bypass,
// because SQL will not execute UPDATE$ as UPDATE.
func isWordRune(c rune) bool {
	switch {
	case c >= 'a' && c <= 'z', c >= 'A' && c <= 'Z', c >= '0' && c <= '9':
		return true
	case c == '_', c == '#', c == '$', c == '@':
		return true
	}
	return false
}

// tokenize returns the upper-cased word tokens of an already-masked statement.
func tokenize(masked string) []string {
	var toks []string
	rs := []rune(masked)
	for i := 0; i < len(rs); {
		if !isWordRune(rs[i]) {
			i++
			continue
		}
		j := i
		for j < len(rs) && isWordRune(rs[j]) {
			j++
		}
		toks = append(toks, strings.ToUpper(string(rs[i:j])))
		i = j
	}
	return toks
}
