import DayClient from "../../../components/DayClient";
import { notFound } from "next/navigation";

export const metadata = { title: "One day" };

export default async function Page({ params }: { params: Promise<{ n: string }> }) {
  const { n } = await params;
  const day = Number(n);
  if (!Number.isInteger(day) || day < 1 || day > 31) notFound();
  return <DayClient n={day} />;
}
