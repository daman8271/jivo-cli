// Package hana is the read-only query core: it owns the connection pool and is
// the only place in hana-sql that talks to the database.
//
// Read-only is layered, and this package holds layers 4 and 5:
//
//	layer 0-3  internal/guard — lexer, first-token allowlist, single statement,
//	           banned keywords. Runs BEFORE anything reaches the driver.
//	layer 4    every statement runs inside BeginTx{ReadOnly: true}, which
//	           go-hdb turns into HANA's own "set transaction read only", and
//	           the transaction is ALWAYS rolled back. There is no call to
//	           Commit anywhere in this package — TestNoCommitInPackage proves
//	           it, so the backstop cannot be removed by accident.
//	layer 5    row cap, response byte cap, per-statement deadline (a real
//	           server-side cancel: go-hdb calls session.cancel on ctx.Done)
//	           and an in-flight semaphore, so a model cannot stampede the
//	           production database the business is actually using.
package hana

import (
	"context"
	"crypto/tls"
	"database/sql"
	"errors"
	"fmt"
	"io"
	"strings"
	"sync"
	"time"

	"github.com/SAP/go-hdb/driver"

	"hana-sql/internal/config"
	"hana-sql/internal/guard"
)

// Defaults for the MCP server. The CLI overrides them with "unlimited".
const (
	DefaultMaxRows       = 1000
	DefaultMaxBytes      = 1 << 20 // ~1 MiB of response payload
	DefaultTimeout       = 60 * time.Second
	DefaultMaxConcurrent = 2
	DefaultLobLimit      = 8 << 10 // 8 KiB per LOB cell
)

// Limits are the per-call resource caps. A zero field means "no limit".
type Limits struct {
	MaxRows  int
	MaxBytes int
	Timeout  time.Duration
}

// Options configure the pool and the default limits.
type Options struct {
	Limits
	MaxConcurrent int
	// LobLimit caps each LOB cell. Zero means DefaultLobLimit; a NEGATIVE value
	// means no limit at all, which is what the human CLI asks for — a person
	// running `hana-sql "SELECT DEFINITION FROM SYS.VIEWS …"` wants the whole
	// definition, not 8 KiB of it ending in " …[clipped]".
	LobLimit int
	// AppName is reported to HANA for audit attribution (M_CONNECTIONS).
	AppName string
	// Log receives one audit line per query. nil means io.Discard.
	Log io.Writer
}

// Result is one tabular answer, already capped and normalized.
type Result struct {
	Columns   []Column         `json:"columns"`
	Rows      []map[string]any `json:"rows"`
	RowCount  int              `json:"row_count"`
	Truncated bool             `json:"truncated"`
	Note      string           `json:"note,omitempty"`
	Elapsed   time.Duration    `json:"-"`
}

// DB is a lazily-connected HANA pool.
//
// New never dials. A momentarily dead reverse tunnel therefore degrades the
// backend (doctor says so, queries fail with a clear message) instead of
// crash-looping the container at startup.
type DB struct {
	cfg  *config.Config
	opts Options

	sem chan struct{}

	// dial opens the pool. Production leaves it nil, which means "dial HANA
	// with go-hdb". The unit tests replace it with an in-memory driver so the
	// layer-4 transaction and the layer-5 caps are exercised with no database
	// in the process; nothing else in the package may set it.
	dial func(context.Context) (*sql.DB, string, error)

	// dialMu serialises dialling. It is deliberately NOT mu: a dial can take
	// tens of seconds when the office tunnel is down, and holding the state lock
	// for that long put Mode() and hana_doctor behind it.
	dialMu sync.Mutex

	// mu guards the three fields below and is never held across a dial.
	mu     sync.Mutex
	db     *sql.DB
	mode   string // "plaintext" or "TLS"
	closed bool
}

// New builds a DB. It does not connect.
func New(cfg *config.Config, opts Options) *DB {
	if opts.MaxConcurrent <= 0 {
		opts.MaxConcurrent = DefaultMaxConcurrent
	}
	if opts.LobLimit == 0 {
		opts.LobLimit = DefaultLobLimit
	}
	if opts.AppName == "" {
		opts.AppName = "hana-sql"
	}
	if opts.Log == nil {
		opts.Log = io.Discard
	}
	return &DB{
		cfg:  cfg,
		opts: opts,
		sem:  make(chan struct{}, opts.MaxConcurrent),
	}
}

// Config exposes the resolved credentials holder (for scrubbing and doctor).
func (d *DB) Config() *config.Config { return d.cfg }

// Limits returns the configured default caps.
func (d *DB) Limits() Limits { return d.opts.Limits }

// MaxConcurrent returns the in-flight cap.
func (d *DB) MaxConcurrent() int { return d.opts.MaxConcurrent }

// Mode reports how the live connection was established ("plaintext", "TLS", or
// "" when nothing has connected yet).
func (d *DB) Mode() string {
	d.mu.Lock()
	defer d.mu.Unlock()
	return d.mode
}

// Close releases the pool if one was opened.
func (d *DB) Close() error {
	d.mu.Lock()
	db := d.db
	d.db, d.mode, d.closed = nil, "", true
	d.mu.Unlock()
	if db == nil {
		return nil
	}
	return db.Close()
}

// Pool returns the live pool, dialling on first use. It tries plaintext then
// TLS, exactly as the CLI always has, and reports which one worked.
//
// Only the dial is serialised (dialMu); the state lock is taken for the two
// short reads/writes around it, so a caller asking Mode() — or hana_doctor
// reporting the connection — is never queued behind a 40s dial into a dead
// tunnel.
func (d *DB) Pool(ctx context.Context) (*sql.DB, string, error) {
	if db, mode := d.current(); db != nil {
		return db, mode, nil
	}

	d.dialMu.Lock()
	defer d.dialMu.Unlock()
	// Another caller may have dialled while we waited for dialMu.
	if db, mode := d.current(); db != nil {
		return db, mode, nil
	}

	db, mode, err := d.dialOnce(ctx)
	if err != nil {
		return nil, "", err
	}

	d.mu.Lock()
	if d.closed {
		d.mu.Unlock()
		db.Close()
		return nil, "", errors.New("connection pool is closed")
	}
	d.db, d.mode = db, mode
	d.mu.Unlock()
	return db, mode, nil
}

// current returns the live pool without dialling.
func (d *DB) current() (*sql.DB, string) {
	d.mu.Lock()
	defer d.mu.Unlock()
	return d.db, d.mode
}

// dialOnce opens one pool. It never touches d.mu, so it may be slow.
func (d *DB) dialOnce(ctx context.Context) (*sql.DB, string, error) {
	if d.dial != nil {
		return d.dial(ctx)
	}
	if err := d.cfg.Validate(); err != nil {
		return nil, "", err
	}

	var lastErr error
	for _, useTLS := range []bool{false, true} {
		c := driver.NewBasicAuthConnector(d.cfg.Addr(), d.cfg.User, d.cfg.Password)
		// The socket timeout must outlive the statement deadline, or the
		// connection dies before the statement can be cancelled cleanly.
		c.SetTimeout(d.socketTimeout())
		c.SetApplicationName(d.opts.AppName)
		if useTLS {
			c.SetTLSConfig(&tls.Config{InsecureSkipVerify: true}) //nolint:gosec // private tunnel, self-signed cert
		}
		db := sql.OpenDB(c)
		// A tunnel that dies leaves poisoned idle connections behind, so keep
		// the pool small and recycle it.
		db.SetMaxOpenConns(4)
		db.SetMaxIdleConns(2)
		db.SetConnMaxIdleTime(30 * time.Second)
		db.SetConnMaxLifetime(5 * time.Minute)

		probeCtx, cancel := context.WithTimeout(ctx, dialProbeTimeout)
		var one int
		err := db.QueryRowContext(probeCtx, "SELECT 1 FROM DUMMY").Scan(&one)
		cancel()
		if err == nil {
			mode := "plaintext"
			if useTLS {
				mode = "TLS"
			}
			return db, mode, nil
		}
		lastErr = err
		db.Close()
		// The caller's own context died (its deadline, or the client went away):
		// stop here rather than spending another probe on a TLS attempt that
		// cannot succeed either, and let run() report the right error class.
		if ctx.Err() != nil {
			return nil, "", ctx.Err()
		}
	}
	return nil, "", fmt.Errorf("could not connect to HANA at %s (tried plaintext and TLS): %s",
		d.cfg.Addr(), d.cfg.ScrubErr(lastErr))
}

// dialProbeTimeout bounds ONE connection probe (plaintext, then TLS).
const dialProbeTimeout = 20 * time.Second

func (d *DB) socketTimeout() time.Duration {
	if d.opts.Timeout <= 0 {
		return 90 * time.Second
	}
	return d.opts.Timeout + 30*time.Second
}

// resolve merges per-call limits over the configured defaults. A caller may
// only tighten a limit that is already set, never loosen it past the ceiling.
func (d *DB) resolve(l Limits) Limits {
	out := d.opts.Limits
	if l.MaxRows > 0 && (out.MaxRows <= 0 || l.MaxRows < out.MaxRows) {
		out.MaxRows = l.MaxRows
	}
	if l.MaxBytes > 0 && (out.MaxBytes <= 0 || l.MaxBytes < out.MaxBytes) {
		out.MaxBytes = l.MaxBytes
	}
	if l.Timeout > 0 && (out.Timeout <= 0 || l.Timeout < out.Timeout) {
		out.Timeout = l.Timeout
	}
	return out
}

// QueryReadOnly is one of exactly two entry points that send SQL to HANA (the
// other is StreamReadOnly); both go through run, so the layered sequence exists
// in exactly one place.
//
// args are bound as real parameters; the statement text is never built by
// string concatenation of caller input anywhere in this package.
func (d *DB) QueryReadOnly(ctx context.Context, p guard.Policy, lim Limits, stmt string, args ...any) (*Result, error) {
	return d.queryReadOnly(ctx, p, lim, aggregateAdvice, stmt, args...)
}

// capAdvice is the sentence appended to the row-cap note. It is a parameter
// because the right advice depends on what was being read: "aggregate
// server-side" is correct for a business query and useless for a catalog
// listing, where there is nothing to aggregate and the caller needs a way to
// page instead.
type capAdvice string

const (
	aggregateAdvice capAdvice = "aggregate server-side with SUM/COUNT/GROUP BY instead of paging rows"
	catalogAdvice   capAdvice = "this listing is a catalog page, not something you can aggregate: narrow it with `like`, ask for one `schema` at a time, or fetch the next page with `offset`"
)

// CatalogTruncationAdvice and QueryTruncationAdvice expose the two truncation
// steers so a test in another package can assert the catalog never inherits the
// "aggregate server-side" advice, which is impossible to follow for a table
// listing and was the misdirection half of the partial-catalog defect.
func CatalogTruncationAdvice() string { return string(catalogAdvice) }
func QueryTruncationAdvice() string   { return string(aggregateAdvice) }

// queryReadOnly is QueryReadOnly with the truncation advice chosen by the caller.
func (d *DB) queryReadOnly(ctx context.Context, p guard.Policy, lim Limits, advice capAdvice, stmt string, args ...any) (*Result, error) {
	return d.run(ctx, p, lim, stmt, args, func(rows *sql.Rows, lim Limits) (*Result, error) {
		return d.scan(rows, lim, advice)
	})
}

// StreamReadOnly is the CLI's entry point: same guard, same READ ONLY
// transaction, same rollback — but rows are handed to onRow as they arrive
// instead of being buffered, so `hana-sql "SELECT * FROM …"` cannot be turned
// into an out-of-memory by a large table. onCols is called once, before the
// first row.
func (d *DB) StreamReadOnly(ctx context.Context, p guard.Policy, lim Limits, stmt string, args []any,
	onCols func([]Column) error, onRow func(map[string]any) error) error {
	_, err := d.run(ctx, p, lim, stmt, args, func(rows *sql.Rows, lim Limits) (*Result, error) {
		return d.stream(rows, lim, aggregateAdvice, onCols, onRow)
	})
	return err
}

// run is THE read-only pipeline. Order of operations, none of which may be
// reordered:
//
//	guard.Check -> deadline -> semaphore -> READ ONLY tx -> query -> rollback
//
// The deadline is applied BEFORE the semaphore on purpose. It used to be the
// other way round, which meant a caller asking for timeout_ms:100 behind one
// in-flight 1.5s query waited 1.501s: its own deadline did not bound the queue,
// only the statement. Worse, a client that had already given up (HTTP
// disconnect, gateway timeout) still eventually ran its query against production
// HANA. With the deadline first, a queued call gives up on its own terms and
// nothing is ever sent.
//
// Every statement this process sends to HANA passes through this function.
func (d *DB) run(ctx context.Context, p guard.Policy, lim Limits, stmt string, args []any,
	consume func(*sql.Rows, Limits) (*Result, error)) (*Result, error) {
	start := time.Now()

	if err := guard.Check(stmt, p); err != nil { // layers 0-3
		d.audit("refused", p, stmt, nil, time.Since(start), err)
		return nil, err
	}

	// Layer 5b — statement deadline. go-hdb turns ctx.Done into a real
	// server-side cancel, so this bounds HANA CPU, not just our wait. It also
	// bounds the queue wait below.
	lim = d.resolve(lim)
	if lim.Timeout > 0 {
		var cancel context.CancelFunc
		ctx, cancel = context.WithTimeout(ctx, lim.Timeout)
		defer cancel()
	}

	// Layer 5a — in-flight cap.
	select {
	case d.sem <- struct{}{}:
		defer func() { <-d.sem }()
	case <-ctx.Done():
		err := d.queueErr(ctx, lim)
		d.audit("error", p, stmt, nil, time.Since(start), err)
		return nil, err
	}

	pool, _, err := d.Pool(ctx)
	if err != nil {
		err = d.wrapDial(ctx, err, lim.Timeout)
		d.audit("error", p, stmt, nil, time.Since(start), err)
		return nil, err
	}

	// Layer 4 — HANA's own read-only access mode. ALWAYS rolled back; this
	// package never commits.
	tx, err := pool.BeginTx(ctx, &sql.TxOptions{ReadOnly: true, Isolation: sql.LevelReadCommitted})
	if err != nil {
		err = d.wrap(err)
		d.audit("error", p, stmt, nil, time.Since(start), err)
		return nil, err
	}
	defer tx.Rollback() //nolint:errcheck // read-only tx; rollback is the only exit

	rows, err := tx.QueryContext(ctx, stmt, args...)
	if err != nil {
		err = d.wrap(err)
		d.audit("error", p, stmt, nil, time.Since(start), err)
		return nil, err
	}
	defer rows.Close()

	res, err := consume(rows, lim)
	if err != nil {
		err = d.wrap(err)
		d.audit("error", p, stmt, nil, time.Since(start), err)
		return nil, err
	}
	res.Elapsed = time.Since(start)
	d.audit("accepted", p, stmt, res, res.Elapsed, nil)
	return res, nil
}

// scan reads the whole result set into memory under the row and byte caps.
func (d *DB) scan(rows *sql.Rows, lim Limits, advice capAdvice) (*Result, error) {
	res := &Result{Rows: []map[string]any{}}
	err := d.walk(rows, lim, advice, res,
		func(cols []Column) error { res.Columns = cols; return nil },
		func(m map[string]any) error { res.Rows = append(res.Rows, m); return nil })
	if err != nil {
		return nil, err
	}
	res.RowCount = len(res.Rows)
	return res, nil
}

// stream reads the result set row by row, handing each to onRow. It shares
// walk with scan, so the caps and the LOB handling behave identically.
func (d *DB) stream(rows *sql.Rows, lim Limits, advice capAdvice, onCols func([]Column) error, onRow func(map[string]any) error) (*Result, error) {
	res := &Result{}
	n := 0
	err := d.walk(rows, lim, advice, res,
		func(cols []Column) error { res.Columns = cols; return onCols(cols) },
		func(m map[string]any) error { n++; return onRow(m) })
	if err != nil {
		return nil, err
	}
	res.RowCount = n
	return res, nil
}

// walk is the shared read loop: build the scan plans from the driver's column
// metadata, then emit normalized rows until the result set ends or a layer-5
// cap trips. It sets Truncated/Note on res; the caller owns RowCount.
func (d *DB) walk(rows *sql.Rows, lim Limits, advice capAdvice, res *Result,
	onCols func([]Column) error, onRow func(map[string]any) error) error {
	names, err := rows.Columns()
	if err != nil {
		return err
	}
	cts, err := rows.ColumnTypes()
	if err != nil {
		return err
	}
	plans := newColPlans(names, cts, d.opts.LobLimit)

	dest := make([]any, len(plans))
	cols := make([]Column, len(plans))
	for i, p := range plans {
		dest[i] = p.dest()
		cols[i] = p.col
	}
	if err := onCols(cols); err != nil {
		return err
	}

	var (
		emitted    int
		bytesUsed  int
		rowCapped  bool
		byteCapped bool
		lobClipped bool
	)
	// Both caps are checked BEFORE the row is consumed, so `truncated` means
	// exactly one thing: there was at least one more row and the caller is not
	// seeing it. Checking the byte cap after appending made a result set that
	// happened to end on the cap report truncated:true with nothing cut — the
	// two cap paths disagreeing about what truncation means is precisely how a
	// caller learns to distrust the flag.
	for rows.Next() {
		if lim.MaxRows > 0 && emitted >= lim.MaxRows {
			rowCapped = true
			break
		}
		if lim.MaxBytes > 0 && bytesUsed >= lim.MaxBytes {
			byteCapped = true
			break
		}
		for _, p := range plans {
			p.reset()
		}
		if err := rows.Scan(dest...); err != nil {
			return err
		}
		m := make(map[string]any, len(plans))
		size := 0
		for _, p := range plans {
			v := p.render()
			m[p.col.Name] = v
			size += len(p.col.Name) + approxSize(v) + 4
			if p.isLob && p.buf.clipped {
				lobClipped = true
			}
		}
		if err := onRow(m); err != nil {
			return err
		}
		emitted++
		bytesUsed += size
	}
	if err := rows.Err(); err != nil {
		return err
	}

	res.Truncated = rowCapped || byteCapped
	var notes []string
	switch {
	case rowCapped:
		notes = append(notes, fmt.Sprintf("row cap reached (%d rows), so this answer is INCOMPLETE; %s", lim.MaxRows, advice))
	case byteCapped:
		notes = append(notes, fmt.Sprintf("response byte cap reached (~%d bytes), so this answer is INCOMPLETE; select fewer columns, or %s", lim.MaxBytes, advice))
	}
	if lobClipped {
		notes = append(notes, fmt.Sprintf("a large text/LOB value was clipped at %d bytes", d.opts.LobLimit))
	}
	res.Note = strings.Join(notes, "; ")
	return nil
}

// queueErr explains a call that died waiting for a free slot, so the caller can
// tell "the server is busy" from "my query is slow". Nothing was sent to HANA.
func (d *DB) queueErr(ctx context.Context, lim Limits) error {
	if errors.Is(ctx.Err(), context.DeadlineExceeded) {
		return fmt.Errorf("timed out after %s waiting for a free query slot — %d queries may run at once (max_concurrent) and this call's own deadline elapsed before it could start; nothing was sent to HANA, so retry with a longer timeout or fewer parallel calls",
			lim.Timeout, d.opts.MaxConcurrent)
	}
	return fmt.Errorf("cancelled while waiting for a free query slot (max_concurrent=%d); nothing was sent to HANA", d.opts.MaxConcurrent)
}

// wrapDial names the phase a failure happened in. A short per-call timeout that
// elapses while the FIRST connection is being opened used to surface as "could
// not connect to HANA (tried plaintext and TLS)", which blames the office tunnel
// for the caller's own limit and sends whoever is on call to the wrong place.
func (d *DB) wrapDial(ctx context.Context, err error, timeout time.Duration) error {
	if err == nil {
		return nil
	}
	msg := d.cfg.ScrubErr(err)
	switch {
	case errors.Is(err, context.DeadlineExceeded) || errors.Is(ctx.Err(), context.DeadlineExceeded):
		return fmt.Errorf("timed out opening the HANA connection: this call's own deadline (%s) elapsed during connection SETUP, not while running the statement — HANA itself may be perfectly reachable, and the first call after startup pays for the connection. Retry, or raise the timeout. Underlying: %s",
			timeout, msg)
	case errors.Is(err, context.Canceled) || errors.Is(ctx.Err(), context.Canceled):
		return fmt.Errorf("cancelled while opening the HANA connection (the caller went away): %s", msg)
	}
	return errors.New(msg)
}

// wrap scrubs the credential out of a driver error and adds a hint for the
// mistake an AI client makes most: an unqualified table name.
func (d *DB) wrap(err error) error {
	if err == nil {
		return nil
	}
	msg := d.cfg.ScrubErr(err)
	if errors.Is(err, context.DeadlineExceeded) {
		return fmt.Errorf("query timed out and was cancelled server-side: %s", msg)
	}
	if strings.Contains(strings.ToLower(msg), "invalid table name") {
		return fmt.Errorf("%s — hint: table names must be schema-qualified and double-quoted, e.g. \"JIVO_OIL_HANADB\".\"OINV\" (the three schemas are JIVO_OIL_HANADB, JIVO_MART_HANADB, JIVO_BEVERAGES_HANADB)", msg)
	}
	return errors.New(msg)
}

// audit writes one line per call: verdict, policy, rows, elapsed, error class
// and the first 500 characters of the statement, always scrubbed.
func (d *DB) audit(verdict string, p guard.Policy, stmt string, res *Result, elapsed time.Duration, err error) {
	if d.opts.Log == nil || d.opts.Log == io.Discard {
		return
	}
	rows, truncated := 0, false
	if res != nil {
		rows, truncated = res.RowCount, res.Truncated
	}
	errClass := "-"
	if err != nil {
		errClass = firstLine(d.cfg.Scrub(err.Error()))
	}
	fmt.Fprintf(d.opts.Log, "hana-sql audit ts=%s verdict=%s policy=%s rows=%d truncated=%t elapsed=%s err=%q sql=%q\n",
		time.Now().Format(time.RFC3339), verdict, p.Name, rows, truncated,
		elapsed.Round(time.Millisecond), errClass, clip(d.cfg.Scrub(collapse(stmt)), 500))
}

func firstLine(s string) string {
	if i := strings.IndexByte(s, '\n'); i >= 0 {
		return s[:i]
	}
	return s
}

func collapse(s string) string { return strings.Join(strings.Fields(s), " ") }

func clip(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "…"
}
