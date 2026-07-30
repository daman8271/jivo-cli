package main

import (
	"crypto/rand"
	"encoding/hex"
	"fmt"
)

// newRequestID mints the per-request UUID the portal sends as x-client-request-id
// and folds into the request signature. Local-only: it never leaves this process
// except as that header, and it is not a credential.
func newRequestID() string {
	var b [16]byte
	if _, err := rand.Read(b[:]); err != nil {
		return "00000000-0000-4000-8000-000000000000"
	}
	b[6] = (b[6] & 0x0f) | 0x40 // version 4
	b[8] = (b[8] & 0x3f) | 0x80 // variant 10
	h := hex.EncodeToString(b[:])
	return fmt.Sprintf("%s-%s-%s-%s-%s", h[0:8], h[8:12], h[12:16], h[16:20], h[20:32])
}
