import AssumptionsClient from "../../components/AssumptionsClient";

export const metadata = {
  title: "Taken as fact",
  description:
    "Why the plan says what it says: what the plant has ruled, what the computer filled in for itself, the speed " +
    "behind every machine, and the questions still waiting for an answer.",
};

// No data at build time, by design — the client reads plan/assumptions.json.
export default function Page() {
  return <AssumptionsClient />;
}
