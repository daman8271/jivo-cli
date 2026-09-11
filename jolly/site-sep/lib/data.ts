import fs from "fs";
import path from "path";
import type {
  Overview, SpineDay, DayDetail, LinesData, StorageData, MaterialsData,
  BuildData, WaData, ScenariosData, LoopsData, HonestyData, QuestionsData,
} from "./types";

// data/ is written ONLY by scripts/gen-data.py from the verified artifacts.
const P = (f: string) => path.join(process.cwd(), "data", f);
const J = <T,>(f: string): T => JSON.parse(fs.readFileSync(P(f), "utf8"));

export const getOverview = () => J<Overview>("overview.json");
export const getSpine = () => J<SpineDay[]>("spine.json");
export const getDay = (n: number) => J<DayDetail>(path.join("days", `day-${String(n).padStart(2, "0")}.json`));
export const getAllDays = () => getSpine().map((d) => getDay(d.n));
export const getLines = () => J<LinesData>("lines.json");
export const getStorage = () => J<StorageData>("storage.json");
export const getMaterials = () => J<MaterialsData>("materials.json");
export const getBuild = () => J<BuildData>("build.json");
export const getWhatsapp = () => J<WaData>("whatsapp.json");
export const getScenarios = () => J<ScenariosData>("scenarios.json");
export const getLoops = () => J<LoopsData>("loops.json");
export const getHonesty = () => J<HonestyData>("honesty.json");
export const getQuestions = () => J<QuestionsData>("questions.json");

// ---- formatting (INR, Indian grouping, litres) ------------------------------
export const fmt = (n: number) => Math.round(n).toLocaleString("en-IN");
export const cr = (rs: number) => `₹${(rs / 1e7).toFixed(2)} Cr`;
// "lakh" spelled out — on a litres-heavy site "₹x.x L" reads as litres (same call the order-by lane made).
export const lakh = (rs: number) => `₹${(rs / 1e5).toFixed(2)} lakh`;
export const money = (rs: number) => (Math.abs(rs) >= 1e7 ? cr(rs) : Math.abs(rs) >= 1e5 ? lakh(rs) : `₹${fmt(rs)}`);
export const litres = (l: number) => `${fmt(l)} L`;
// Small counts as words, so copy like "the two-day lag" stays computed from data
// rather than typed (site rule: no hand-typed business numbers, word-form included).
const COUNT_WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten"];
export const countWord = (n: number) => (Number.isInteger(n) && n >= 0 && n <= 10 ? COUNT_WORDS[n] : fmt(n));
export const tonnes = (l: number) => `${((l * 0.91) / 1000).toFixed(1)} T`; // oil tonnes = litres × 0.91 / 1000

const MON = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
export const dlabel = (iso: string) => `${Number(iso.slice(8, 10))} ${MON[Number(iso.slice(5, 7)) - 1]}`;

// ---- plain-language helpers — defined in ./types (pure, client-safe), re-exported
// here so server pages get them from the same import as the data and formatters.
export {
  PLAIN_KIND, plainKind, plainChannel, PLAIN_EVENT, plainEvent, lakhCrore, litresProse, rupeesProse,
  plural, joinAnd, packWords, packSizesWords, materialWord, speedFraction, speedPhrase, slotNames,
  plainWords, plainHonestyNote,
} from "./types";
export type { HonestyFacts } from "./types";
