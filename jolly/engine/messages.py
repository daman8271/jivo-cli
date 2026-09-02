#!/usr/bin/env python3
"""
THE MESSAGE LAYER v3 — what the planner would send, day by day.

Daman, 2026-08-31: "Gautam is responsible for what to run on what machine, so you need
to teach him: 'Gautam, run this on this machine.' Every day you give him a daily plan,
and that plan changes every day as POs land."

So Gautam gets a BUILD LIST EVERY WORKING DAY — per machine, in sequence, with the oil
and the changeover called out. Everyone else is exception-driven: a message goes out
only when a human must act. Routine ordering is not a message; the system just orders.

INPUT SELECTION (same convention as august_sim.py):
    SIM_INPUTS=sim/sep-inputs.json SIM_TAG=-sep python3 engine/messages.py
reads sim/days-sep/*.json + sim/events-sep.json, writes sim/whatsapp-sep.json.
Default (no env) is the August backtest, byte-compatible with the deployed site.

HONESTY:
  - August (backtest): outgoing = what the planner would have sent (assumed:false,
    the site banners it); replies were WRITTEN IN by the simulation, assumed:true.
  - FORWARD months (actuals_for_scoring.made_l == 0, e.g. September): NOTHING has been
    sent and NOBODY has replied. Every message object carries assumed:true at the DATA
    layer, and there are NO reply objects at all. A previous build showed invented
    replies as real messages from real people with their real numbers — never again.
"""
import glob, json, collections, os
from datetime import date

INPUTS = os.environ.get("SIM_INPUTS", "sim/sim-inputs.json")
TAG = os.environ.get("SIM_TAG", "")
S = json.load(open(INPUTS))
E = json.load(open(f"sim/events{TAG}.json"))
days = [json.load(open(fp)) for fp in sorted(glob.glob(f"sim/days{TAG}/day-*.json"))]
byday = {d["date"]: d for d in days}
P = {p["name"]: p for p in S["people"]}

# forward plan = the month has not happened: every send is simulated, no replies exist
FORWARD = float(S["actuals_for_scoring"]["made_l"] or 0) == 0

def person(*names):
    for n in names:
        for k, v in P.items():
            if n.lower() in k.lower(): return v
    return None
GAUTAM = person("Gautam"); KULBIR = person("Kulbir"); GINNI = person("Bhupinder")
GOPI = person("Gopi", "Gurpreet"); SHUNTY = person("Ravinder", "Shunty") or GOPI
GV = person("Gurvinderjeet"); RAJU = person("Jasbir", "Raju"); PRESHIT = person("Preshit")

threads = collections.defaultdict(list); seen = set()
def msg(to, day, text, reply=None, tag=""):
    if not to: return
    k = (to["whatsapp"], day, text[:44])
    if k in seen: return
    seen.add(k)
    threads[to["whatsapp"]].append(dict(day=day, dir="out", text=text, tag=tag, assumed=FORWARD))
    # a reply is a fabrication unless the month actually ran and the site labels it
    if reply and not FORWARD:
        threads[to["whatsapp"]].append(dict(day=day, dir="in", text=reply, tag=tag, assumed=True))

def L(n): return f"{n:,.0f}"
DN = lambda iso: date.fromisoformat(iso).strftime("%d %b")

# ---- 1. GAUTAM: the daily build list, every working day ------------------------
for d in days:
    if not d["working"] or not d["runs"]: continue
    lines = collections.OrderedDict()
    for r in d["runs"]: lines.setdefault(r["line"], []).append(r)
    parts = []
    for ln, rs in lines.items():
        seq = " → ".join(f"{r['sku'][:26]} {L(r['pieces'])} pcs ({r['hours']:.1f}h)"
                         + (f" ⚑flush {r['flush_min']}min" if r["flush_min"] else "") for r in rs[:4])
        extra = f" +{len(rs)-4} more" if len(rs) > 4 else ""
        parts.append(f"*{ln}* ({d['line_hours'][ln]:.1f}h): {seq}{extra}")
    chg = [b for b in d["blocked"][:3]]
    tail = ""
    if chg:
        tail = "\n\nRuk raha hai: " + ", ".join(f"{b['sku'][:22]} ({b['binder_name'][:22]})" for b in chg)
    # never announce a FORECAST slice as "Kal PO aaya" — a forecast is not an order,
    # whatever its value (September's stream is ~60% channel=FORECAST rows)
    newpo = [n for n in d["new_orders"] if n["value"] >= 3_000_000 and n.get("channel") != "FORECAST"][:2]
    if newpo:
        # day 1's "new" orders are the standing backlog entering the book — old paper,
        # not yesterday's news; only later days may say a PO just came
        if FORWARD:
            # forward month: a dated order enters the book ON its date (news landing,
            # not hindsight) — day 1's stream is the standing backlog, old paper
            lead_in = "Order book pe hai: " if d["date"] == days[0]["date"] else "Aaj naya PO hai: "
        else:
            lead_in = "Kal PO aaya: "
        tail += "\n\n" + lead_in + ", ".join(f"{n['sku'][:24]} {L(n['pieces'])} pcs" for n in newpo) + " — isliye aaj priority badli hai."
    msg(GAUTAM, d["date"],
        f"*{DN(d['date'])} ka plan* — {L(d['made_litres'])} L, lines {d['line_util']}%\n\n" + "\n".join(parts) + tail,
        reply=("Ok ji, laga deta hoon." if d["line_util"] >= 90 else "Theek hai, material ka wait hai."),
        tag="build-list")

# ---- 2. Exception messages ------------------------------------------------------
last = {}
for e in E:
    d = e["day"]; dd = byday[d]
    if e["kind"] == "PACKAGING_ZERO":
        if last.get("pm") and (date.fromisoformat(d) - date.fromisoformat(last["pm"])).days < 4: continue
        last["pm"] = d; its = e["items"][:4]
        if FORWARD:
            # dedupe (the block list repeats an item per placement attempt), and do not
            # ask for an order when a live PO is already booked to land — chase it instead
            uniq, seenk = [], set()
            for i in e["items"]:
                kk = (i["code"], i["sku"])
                if kk in seenk: continue
                seenk.add(kk); uniq.append(i)
            its = uniq[:4]
            def _inb(code):
                for dd in sorted(S["inbound_prebooked"]):
                    if dd >= d and S["inbound_prebooked"][dd].get(code): return dd
                return None
            lines_ = []
            for i in its:
                due = _inb(i["code"])
                note = f" (PO laga hai, {DN(due)} ko aana hai — chase kar lo)" if due else ""
                lines_.append(f"• {i['code']} {i['name'][:34]} — {i['sku'][:28]} ke liye {L(i['want'])} pcs{note}")
            need_order = [i for i in its if not _inb(i["code"])]
            ask = ("\nJinka PO nahi laga, order kar do please — 6 din ka lead hai."
                   if need_order else "\nSab pe PO laga hai — bas aane ki date pakki karwa lo.")
            msg(KULBIR, d, "Kulbir veerji, yeh packaging ZERO pe hai aur line rok rahi hai:\n" +
                "\n".join(lines_) + ask, tag="packaging-zero")
        else:
            msg(KULBIR, d, "Kulbir veerji, yeh packaging ZERO pe hai aur line rok rahi hai:\n" +
                "\n".join(f"• {i['code']} {i['name'][:34]} — {i['sku'][:28]} ke liye {L(i['want'])} pcs" for i in its) +
                "\nOrder kar do please, 6 din ka lead hai.",
                reply=f"Kar diya — {its[0]['name'][:24]} 6 din mein.", tag="packaging-zero")
    elif e["kind"] == "ORDERED_BLOCKER":
        if last.get("ob") and (date.fromisoformat(d) - date.fromisoformat(last["ob"])).days < 5: continue
        last["ob"] = d
        who = SHUNTY if e["code"].startswith("RM") else KULBIR
        msg(who, d, f"{e['name'][:34]} zero pe tha — {L(e['qty'])} ka order nikal diya, "
                    f"{e['lands'][8:10]} {DN(e['lands'])[3:]} tak aa jayega ({e['lead']} din). "
                    f"Tab tak doosra SKU line pe chala rahe hain.",
            reply="Theek hai, confirm kar deta hoon.", tag="ordered")
    elif e["kind"] == "UNBLOCKED":
        if last.get("un") and (date.fromisoformat(d) - date.fromisoformat(last["un"])).days < 4: continue
        last["un"] = d
        msg(GAUTAM, d, f"{e['name'][:36]} aa gaya ({e['waited_days']} din baad). "
                       f"Jo SKU ruka hua tha woh aaj se line pe chalega.",
            reply="Ok, aaj hi lagata hoon.", tag="unblocked")
    elif e["kind"] == "OIL_SHORT":
        if last.get("rm") and (date.fromisoformat(d) - date.fromisoformat(last["rm"])).days < 6: continue
        last["rm"] = d
        msg(SHUNTY, d, "Shunty veerji, oil short:\n" +
            "\n".join(f"• {i['name'][:34]} — {i['sku'][:26]}" for i in e["items"][:3]) +
            "\nOrder nikal diya hai, 11 din. Koi jaldi source ho toh batao.",
            reply="Arora se dekh leta hoon.", tag="oil-short")
    elif e["kind"] == "STORAGE_THROTTLE":
        if last.get("st"): continue
        last["st"] = d
        msg(GOPI, d, f"Gopi bhai, godown {e['pct_start_of_day']}% pe hai — jo bill kat gaye hain "
                     f"unki gaadi aaj hi lagwao, warna production rokna padega.",
            reply="Haan, gaadi laga di hain.", tag="storage")

# ---- 3. Weekly to Gurvinderjeet (+ August's one real decision, August only) ------
D0 = days[0]["date"]
saturdays = [d["date"] for d in days if d["weekday"] == "Saturday"
             and (date.fromisoformat(d["date"]) - date.fromisoformat(D0)).days >= 3]
AUG_TAIL = " Storage ab problem nahi hai — material aur line hours hi limit hain." if not TAG else ""
for wk, d in enumerate(saturdays[:5], 1):
    upto = [x for x in days if x["date"] <= d]
    tot = sum(x["made_litres"] for x in upto); val = sum(x["made_value"] for x in upto)
    util = round(sum(x["line_util"] for x in upto if x["working"]) / max(1, sum(1 for x in upto if x["working"])))
    msg(GV, d, f"Veerji, week {wk}: {L(tot)} L bana, ₹{val/1e7:.1f} Cr. Lines {util}% pe, "
               f"godown {byday[d]['storage']['pct']:.0f}%." + AUG_TAIL, tag="weekly")
if not FORWARD and not TAG:
    # the August decision thread is part of the calibrated backtest narrative; a forward
    # month must not invent a conversation that never happened
    msg(GV, "2026-08-06",
        "Veerji, ek decision. Packaging baar baar zero ho raha hai — labels aur caps ke liye har hafte "
        "line rukti hai. Do raste: (1) har item ka 15 din ka buffer rakhein, ya (2) Kulbir veerji ko "
        "hafte ka forecast bhejein taaki woh pehle order kar sakein. Kya karein?",
        reply="Forecast bhejo. Buffer mein paisa fasta hai.", tag="decision")
    msg(PRESHIT, "2026-08-07",
        "Preshit bhai, veerji ne bola weekly packaging forecast bhejna hai. Main har Monday nikal doonga — "
        "agle 15 din mein kya chahiye, kis SKU ke liye. Aap Kulbir veerji ke saath review kar lena.",
        reply="Haan bhej do, main dekh loonga.", tag="decision")

if FORWARD:
    NOTE = (f"{S['meta']['month']} has not happened. Every message here is what the planner WOULD "
            "send (assumed:true on every object). Nothing was sent, nobody replied, and no reply is "
            "shown — names and numbers are real, the sends are simulated.")
else:
    NOTE = ("The outgoing messages are what the planner would have sent. The replies are written in by "
            "the simulation, not received — nobody in this list was actually messaged in August 2026.")
out = []
for wa, ms in threads.items():
    p = next(x for x in S["people"] if x["whatsapp"] == wa)
    ms.sort(key=lambda m: m["day"])
    out.append(dict(name=p["name"], whatsapp=wa, display=p["display"], title=p["title"],
                    messages=ms, count=sum(1 for m in ms if m["dir"] == "out")))
out.sort(key=lambda t: -t["count"])
json.dump(out, open(f"sim/whatsapp{TAG}.json", "w"), indent=1)
json.dump(dict(note=NOTE, forward=FORWARD, sent=sum(t["count"] for t in out),
               assumed_sends=sum(1 for t in out for m in t["messages"] if m["dir"] == "out" and m["assumed"]),
               assumed_replies=sum(1 for t in out for m in t["messages"] if m["dir"] == "in")),
          open(f"sim/whatsapp{TAG}-meta.json", "w"), indent=1)
print(f"{'FORWARD (all sends assumed, zero replies)' if FORWARD else 'BACKTEST'} -> sim/whatsapp{TAG}.json")
print(f"{len(out)} threads, {sum(t['count'] for t in out)} sent, "
      f"{sum(1 for t in out for m in t['messages'] if m['dir']=='in')} replies in file")
for t in out: print(f"  {t['name']:<26}{t['display']:<18}{t['count']:>4} msgs")
