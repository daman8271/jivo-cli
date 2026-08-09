package engine

import (
	"archive/zip"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// TmpSuffix marks a bundle that is still being written. Anything carrying it is
// invisible to the listing and to downloads.
const TmpSuffix = ".tmp"

// WriteZip archives a staged tree into dst. Everything inside lands under a
// single jivo-cli/ folder, so the recipient unzips once and gets ~/jivo-cli.
//
// The archive is streamed to dst+".tmp" and renamed into place only once it is
// complete, so a crash or a full disk leaves no half-written credential zip for
// the operator to find, list and send.
//
// Unix modes are carried through zip.FileInfoHeader + SetMode, read from the
// staged files themselves. A plain zip.Create() writes mode-0 entries: every
// Mac binary would extract non-executable and the whole bundle would be dead on
// arrival. archive/zip also writes no __MACOSX sidecars, unlike ditto.
func WriteZip(stageRoot, dst string) (err error) {
	if err := os.MkdirAll(filepath.Dir(dst), 0o755); err != nil {
		return err
	}
	tmp := dst + TmpSuffix
	out, err := os.OpenFile(tmp, os.O_CREATE|os.O_TRUNC|os.O_WRONLY, 0o600)
	if err != nil {
		return err
	}
	// Any failure below leaves nothing behind at either path.
	defer func() {
		if err != nil {
			out.Close()
			os.Remove(tmp)
		}
	}()

	zw := zip.NewWriter(out)

	type entry struct {
		abs  string
		rel  string
		info fs.FileInfo
	}
	var entries []entry
	err = filepath.WalkDir(stageRoot, func(p string, d fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		rel, rerr := filepath.Rel(stageRoot, p)
		if rerr != nil {
			return rerr
		}
		if rel == "." {
			return nil
		}
		info, ierr := d.Info()
		if ierr != nil {
			return ierr
		}
		if info.Mode()&os.ModeSymlink != 0 {
			return fmt.Errorf("zip: refusing to archive symlink %s", rel)
		}
		entries = append(entries, entry{abs: p, rel: filepath.ToSlash(rel), info: info})
		return nil
	})
	if err != nil {
		zw.Close()
		return err
	}
	sort.Slice(entries, func(i, j int) bool { return entries[i].rel < entries[j].rel })

	// The bundle root itself, so extractors that honour directory entries create
	// it even before the first file.
	rootHdr := &zip.FileHeader{Name: BundleRoot + "/"}
	rootHdr.SetMode(0o755 | os.ModeDir)
	if _, err := zw.CreateHeader(rootHdr); err != nil {
		zw.Close()
		return err
	}

	for _, e := range entries {
		hdr, herr := zip.FileInfoHeader(e.info)
		if herr != nil {
			zw.Close()
			return herr
		}
		hdr.Name = zipName(e.rel)
		if e.info.IsDir() {
			hdr.Name += "/"
			hdr.SetMode(e.info.Mode() | os.ModeDir)
			if _, err := zw.CreateHeader(hdr); err != nil {
				zw.Close()
				return err
			}
			continue
		}
		hdr.Method = zip.Deflate
		hdr.SetMode(e.info.Mode().Perm())

		w, cerr := zw.CreateHeader(hdr)
		if cerr != nil {
			zw.Close()
			return cerr
		}
		f, oerr := os.Open(e.abs)
		if oerr != nil {
			zw.Close()
			return oerr
		}
		_, cpErr := io.Copy(w, f)
		f.Close()
		if cpErr != nil {
			zw.Close()
			return cpErr
		}
	}

	if err = zw.Close(); err != nil {
		return err
	}
	if err = out.Sync(); err != nil {
		return err
	}
	if err = out.Close(); err != nil {
		return err
	}
	// Only now does the bundle exist under its real name.
	if err = os.Rename(tmp, dst); err != nil {
		return err
	}
	return nil
}

// IsPartial reports whether a path is a bundle still being written. Listings
// and downloads must skip these.
func IsPartial(name string) bool { return strings.HasSuffix(name, TmpSuffix) }

// SHA256File is the checksum reported with every bundle, so the operator can
// confirm the file the recipient received is the file that was built.
func SHA256File(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

// ZipEntry is one file read back out of a finished archive.
type ZipEntry struct {
	Name string
	Mode os.FileMode
	Size int64
}

// ReadZipEntries reopens an archive and reports what is actually in it. Tests
// use this rather than inspecting the staging directory: the staging modes are
// not evidence that the archive preserved them.
func ReadZipEntries(path string) ([]ZipEntry, error) {
	r, err := zip.OpenReader(path)
	if err != nil {
		return nil, err
	}
	defer r.Close()
	out := make([]ZipEntry, 0, len(r.File))
	for _, f := range r.File {
		out = append(out, ZipEntry{Name: f.Name, Mode: f.Mode(), Size: int64(f.UncompressedSize64)})
	}
	return out, nil
}

// ZipFileContent reads one entry out of an archive by its bundle-relative path.
func ZipFileContent(path, rel string) ([]byte, error) {
	r, err := zip.OpenReader(path)
	if err != nil {
		return nil, err
	}
	defer r.Close()
	want := zipName(rel)
	for _, f := range r.File {
		if f.Name != want {
			continue
		}
		rc, err := f.Open()
		if err != nil {
			return nil, err
		}
		defer rc.Close()
		return io.ReadAll(rc)
	}
	return nil, fmt.Errorf("zip: %s not found in %s", want, filepath.Base(path))
}

// AssertZipClean re-reads a finished archive and refuses it if anything denied,
// or any macOS/editor junk, made it in. This is the last thing that runs before
// a bundle is handed to an operator.
func AssertZipClean(path string) error {
	entries, err := ReadZipEntries(path)
	if err != nil {
		return err
	}
	var problems []string
	for _, e := range entries {
		if !strings.HasPrefix(e.Name, BundleRoot+"/") && e.Name != BundleRoot+"/" {
			problems = append(problems, fmt.Sprintf("%s is outside the %s/ root", e.Name, BundleRoot))
			continue
		}
		rel := strings.TrimPrefix(e.Name, BundleRoot+"/")
		if rel == "" {
			continue
		}
		rel = strings.TrimSuffix(rel, "/")
		if pattern, bad := Denied(rel); bad {
			problems = append(problems, fmt.Sprintf("%s (matched %s)", rel, pattern))
		}
		if strings.HasPrefix(e.Name, "__MACOSX") {
			problems = append(problems, e.Name)
		}
	}
	if len(problems) > 0 {
		return fmt.Errorf("finished zip is not clean: %s", strings.Join(problems, "; "))
	}
	return nil
}
