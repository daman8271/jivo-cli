#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""oms_backfill.py — walk the OMS order book BACKWARDS, once, by hand.

    cd jolly && python3 live/oms_backfill.py --dry-run     # show the plan, call nothing
    cd jolly && python3 live/oms_backfill.py               # the real run, ~9 minutes

RUN IT YOURSELF. It is not in live/loop.sh, no cron calls it, and nothing else
imports it. It is a one-time repair for one specific hole, and it spends ~500
live requests on a server the whole loop is careful with — so it is the owner's
call to make, not an agent's.

THE HOLE
    live/adapters/oms.py walks the order book FORWARD from a cursor, one id at a
    time, because `orders list` shows this billing account only 3 of ~3,100
    orders while `orders detail <id>` has no role filter at all. That works
    perfectly for everything opened from now on. It has one blind spot: the
    cursor was seeded at 3089 on 2026-09-02, so every order opened BEFORE then
    is invisible. The freeze feels it directly — the live demand stream reads
    ~89% expected-not-yet-ordered, and the pile of orders already on the book
    reads 0 documents where the 31-August freeze counted 121. Neither is a quiet
    month. Both are this hole.

WHAT IT DOES
    Probes `orders detail <id>` for a range of ids BELOW the cursor, stores every
    order it finds in live/state/oms.orders.json in exactly the adapter's own
    shape (it calls the adapter's own _fetch_order/_order_record, so there is one
    definition of an order record, not two), and skips ids OMS says do not exist.

WHAT IT DELIBERATELY DOES NOT DO
    * It never moves live/state/oms.cursor. The forward walk owns that file; a
      backfill that pushed the cursor down would make the loop re-walk ids it
      has already settled, and one that pushed it up would skip real orders
      forever.
    * It never re-reads an id already in the store (pass --refetch if you want
      status refreshed) — the cheapest live request is the one not made.
    * It never widens the adapter's read-only allowlist. `orders detail` is on
      it; `account profile` is not, and never will be (its body carries the
      user's password hash).

SAFE TO RUN WHILE THE 3-MINUTE LOOP IS RUNNING
    Every flush re-reads live/state/oms.orders.json, merges our finds into
    whatever is there now, and writes it back through the adapter's own atomic
    tmp+rename. So an order the forward walk adds while we are running is kept,
    not clobbered. The reverse is also true, which is why we flush often.

HOW LONG
    The range is HALF-OPEN, like Python's range(): [--from-id, --to-id). The
    default is the 500 ids immediately below the cursor — cursor-500 .. cursor-1
    — because the cursor itself is already stored. At the default one request a
    second that is 500 requests, about 9 minutes. --rate raises it, but never
    past two a second: the floor of half a second between calls is hard-coded,
    because this is the same OMS the loop has to keep talking to all day.

    --to-id equal to --from-id is an EMPTY range: zero ids, zero calls.

STOPPING IT
    Ctrl-C is a clean exit. Whatever has been found is flushed and the summary
    still prints, so a run stopped halfway is progress kept, not work lost. Run
    it again with --from-id set to where it stopped.

RULE 0 — no SAP anywhere. OMS only, read-only, through the CLI the adapter
already owns.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from collections import Counter

_HERE = os.path.dirname(os.path.abspath(__file__))          # .../jolly/live
_JOLLY = os.path.dirname(_HERE)                             # .../jolly
# jolly/ on the path so the adapter imports under its documented package name,
# exactly the way live/collect.py does it.
if _JOLLY not in sys.path:
    sys.path.insert(0, _JOLLY)

from live.adapters import oms                               # noqa: E402

# Half a second between calls, and no argument can talk it down. The loop has to
# keep using this server every three minutes after we are finished with it.
MIN_GAP_S = 0.5
FLUSH_EVERY = 25          # orders found between writes to disk
STOP_AFTER_ERRORS = 10    # consecutive non-404 failures that end the run


def flush(found: dict) -> int:
    """Merge what we have found into the adapter's store and write it back.

    Re-read, merge, write — never write a copy we loaded minutes ago. The
    3-minute loop may have added orders while we were probing, and its finds
    matter as much as ours.
    """
    if not found:
        return 0
    store = oms._read_json(oms.ORDERS_FILE, {})
    store.update(found)
    oms._write_json(oms.ORDERS_FILE, store)
    return len(store)


def summarise(found_count, missing, errors, probed, seconds, wrote):
    store = oms._read_json(oms.ORDERS_FILE, {})
    buckets, open_total = oms._by_status(store)
    total_litres = sum(float(r.get("litres") or 0) for r in store.values())

    print()
    print("=== oms_backfill ===")
    print(f"  probed {probed} id(s) in {seconds / 60:.1f} min · "
          f"found {found_count} · not there {missing} · failed {errors}")
    print(f"  live/state/oms.orders.json now holds {wrote or len(store)} order(s)")
    print(f"  total litres in the book        {total_litres:>14,.0f} L")
    print(f"  still open (not a closed state) {open_total['count']:>6} order(s) · "
          f"{open_total['litres']:,.0f} L · Rs {open_total['amount_inr']:,.0f}")
    if open_total.get("litres_by_category"):
        print("  open litres by category: " + " · ".join(
            f"{k} {v:,.0f} L" for k, v in sorted(open_total["litres_by_category"].items(),
                                                 key=lambda x: -x[1])))
    print("  every status bucket:")
    for code, bucket in sorted(buckets.items(), key=lambda x: -x[1]["count"]):
        mark = " " if bucket["terminal"] else "*"
        print(f"   {mark} {code:<22} {bucket['count']:>5} order(s)  "
              f"{bucket['litres']:>13,.0f} L  Rs {bucket['amount_inr']:>15,.0f}")
    print("    (* = still open. A status is as at the last time we read that order.)")
    if len(store) > oms.STORE_MAX:
        print(f"  !! the store now holds {len(store)} orders and the adapter trims to "
              f"OMS_STORE_MAX={oms.STORE_MAX} by keeping the HIGHEST ids — the next loop "
              f"cycle would drop exactly what this run backfilled. Raise OMS_STORE_MAX "
              f"in the loop's environment before the next cycle.")
    print("  live/state/oms.cursor was NOT touched — the forward walk still owns it.")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="one-time backward walk of the OMS order book (run it by hand)")
    ap.add_argument("--from-id", type=int, default=None,
                    help="lowest order id to probe (default: the cursor minus --count)")
    ap.add_argument("--to-id", type=int, default=None,
                    help="stop BEFORE this id — the range is half-open [from, to), so "
                         "--to-id equal to --from-id probes nothing (default: the cursor)")
    ap.add_argument("--count", type=int, default=500,
                    help="how many ids below the cursor to take when --from-id is not given")
    ap.add_argument("--rate", type=float, default=1.0,
                    help="requests per second (default 1.0; never faster than 2.0 — there "
                         "is a hard half-second floor between calls)")
    ap.add_argument("--refetch", action="store_true",
                    help="probe ids that are already in the store as well (refreshes status)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan and make no live call at all")
    args = ap.parse_args(argv)

    cursor = oms._read_cursor()
    if cursor is None and (args.from_id is None or args.to_id is None):
        raise SystemExit(
            f"oms_backfill: no cursor at {oms.CURSOR_FILE} yet, so there is nothing to walk "
            f"back from. Let the loop run one cycle, or give both --from-id and --to-id.")
    to_id = args.to_id if args.to_id is not None else cursor
    from_id = args.from_id if args.from_id is not None else max(1, to_id - args.count)
    if from_id > to_id:
        raise SystemExit(f"oms_backfill: --from-id {from_id} is above --to-id {to_id}; "
                         f"the range is [from, to) and this one runs backwards.")

    store = oms._read_json(oms.ORDERS_FILE, {})
    ids = list(range(from_id, to_id))
    todo = ids if args.refetch else [i for i in ids if str(i) not in store]
    gap = max(MIN_GAP_S, 1.0 / args.rate) if args.rate > 0 else MIN_GAP_S

    print(f"oms_backfill — walking the OMS order book backwards")
    print(f"  CLI      {oms.BIN}")
    print(f"  config   {oms.CONFIG}")
    print(f"  store    {oms.ORDERS_FILE}  ({len(store)} order(s) now)")
    print(f"  cursor   {oms.CURSOR_FILE}  (= {cursor}) — NOT touched by this run")
    print(f"  range    [{from_id}, {to_id})  ->  {len(ids)} id(s)")
    print(f"  to probe {len(todo)} id(s)"
          + ("" if args.refetch else f" ({len(ids) - len(todo)} already stored, skipped)"))
    print(f"  pace     {1.0 / gap:.2f}/s ({gap:.2f}s between calls)"
          + (f" — asked for {args.rate}/s, held at the floor" if 1.0 / gap < args.rate else ""))
    print(f"  about    {len(todo) * gap / 60:.1f} minute(s)")
    if not os.path.isfile(oms.BIN):
        print(f"  !! {oms.BIN} is not there — the run would fail on the first call")
    if not os.path.isfile(oms.CONFIG):
        print(f"  !! {oms.CONFIG} is not there — log in first: "
              f"`{oms.BIN} auth login --config {oms.CONFIG}` (Daman@oms.com)")

    if args.dry_run:
        print("  DRY RUN — no live call made, nothing written.")
        return 0
    if not todo:
        print("  nothing to probe. No live call made, nothing written.")
        return 0

    seen_at = oms._iso(oms._now())
    found: dict = {}
    found_count = missing = errors = probed = 0
    run_errors = 0
    started = time.monotonic()
    stopped = None

    try:
        for n, order_id in enumerate(todo, 1):
            if n > 1:
                time.sleep(gap)
            record, kind, error = oms._fetch_order(order_id, seen_at)
            probed += 1
            if kind == "found":
                found[str(order_id)] = record
                found_count += 1
                run_errors = 0
            elif kind == "missing":
                missing += 1
                run_errors = 0
            else:
                errors += 1
                run_errors += 1
                print(f"  [{n}/{len(todo)}] id {order_id}: {error}")
                if run_errors >= STOP_AFTER_ERRORS:
                    stopped = (f"{run_errors} calls in a row failed — stopping rather than "
                               f"hammering OMS. Check the token, then re-run with "
                               f"--from-id {order_id}")
                    break

            if n % 25 == 0 or n == len(todo):
                rate = probed / max(time.monotonic() - started, 0.001)
                left = (len(todo) - n) * gap / 60
                print(f"  [{n}/{len(todo)}] found {found_count} · not there {missing} · "
                      f"failed {errors} · {rate:.2f}/s · ~{left:.1f} min left")
            if len(found) >= FLUSH_EVERY:
                flush(found)
                found = {}
    except KeyboardInterrupt:
        stopped = "stopped by hand (Ctrl-C) — everything found so far is kept"

    wrote = flush(found)
    if stopped:
        print(f"\n  {stopped}")
    summarise(found_count, missing, errors, probed, time.monotonic() - started, wrote)
    return 0


if __name__ == "__main__":
    sys.exit(main())
