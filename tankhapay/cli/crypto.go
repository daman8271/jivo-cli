package main

import (
	"crypto/aes"
	"encoding/base64"
	"errors"
	"strings"
)

// TankhaPay body cipher — AES-128-ECB + PKCS7, base64. Proven live 2026-07-25.
// The whole request body is {"encrypted": base64(AES-ECB(JSON.stringify(payload)))}
// and the response carries commonData = base64(AES-ECB(json)). Go's stdlib has no
// ECB mode (by design — it is insecure), so we drive cipher.Block block-by-block.
// This is not our choice of cryptography; it is what the production API requires,
// reproduced exactly. See ../vault/_meta/Encryption-Scheme.md.

func pkcs7Pad(b []byte, block int) []byte {
	n := block - len(b)%block
	pad := make([]byte, n)
	for i := range pad {
		pad[i] = byte(n)
	}
	return append(b, pad...)
}

func pkcs7Unpad(b []byte, block int) ([]byte, error) {
	if len(b) == 0 || len(b)%block != 0 {
		return nil, errors.New("pkcs7: input not block-aligned")
	}
	n := int(b[len(b)-1])
	if n == 0 || n > block || n > len(b) {
		return nil, errors.New("pkcs7: invalid padding size")
	}
	for _, c := range b[len(b)-n:] {
		if int(c) != n {
			return nil, errors.New("pkcs7: corrupt padding")
		}
	}
	return b[:len(b)-n], nil
}

// aesECBEncrypt encrypts plain with AES-ECB and returns standard base64.
func aesECBEncrypt(key, plain []byte) (string, error) {
	blk, err := aes.NewCipher(key)
	if err != nil {
		return "", err
	}
	bs := blk.BlockSize()
	src := pkcs7Pad(plain, bs)
	out := make([]byte, len(src))
	for i := 0; i < len(src); i += bs {
		blk.Encrypt(out[i:i+bs], src[i:i+bs])
	}
	return base64.StdEncoding.EncodeToString(out), nil
}

// aesECBDecrypt reverses aesECBEncrypt. It tolerates a missing base64 pad and
// URL-safe alphabet, which some fields in the wild use.
func aesECBDecrypt(key []byte, b64 string) ([]byte, error) {
	s := strings.TrimSpace(b64)
	ct, err := base64.StdEncoding.DecodeString(s)
	if err != nil {
		if p := s + strings.Repeat("=", (4-len(s)%4)%4); true {
			if ct, err = base64.StdEncoding.DecodeString(p); err != nil {
				ct, err = base64.URLEncoding.DecodeString(p)
			}
		}
		if err != nil {
			return nil, err
		}
	}
	blk, err := aes.NewCipher(key)
	if err != nil {
		return nil, err
	}
	bs := blk.BlockSize()
	if len(ct) == 0 || len(ct)%bs != 0 {
		return nil, errors.New("ecb: ciphertext not block-aligned")
	}
	out := make([]byte, len(ct))
	for i := 0; i < len(ct); i += bs {
		blk.Decrypt(out[i:i+bs], ct[i:i+bs])
	}
	return pkcs7Unpad(out, bs)
}
