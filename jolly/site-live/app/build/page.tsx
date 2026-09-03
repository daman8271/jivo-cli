import BuildClient from "../../components/BuildClient";
export const metadata = {
  title: "Running now",
  description: "What is on each machine at this minute, beside what the plan would run there.",
};
export default function Page() { return <BuildClient />; }
