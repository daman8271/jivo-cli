import Link from "next/link";

export default function NotFound() {
  return (
    <div className="py-16 text-center">
      <h1 className="text-2xl font-bold">That page is not here</h1>
      <p className="mt-2 text-sm text-zinc-400">
        Check the address — the day pages only go as far as the last day of the plan.
      </p>
      <p className="mt-2 text-sm text-zinc-400">
        If you were after the messages page: that belongs to the old site. The real WhatsApp channel is the Jolly agent,
        not a web page.
      </p>
      <Link href="/" className="mt-4 inline-block text-sm text-amber-400 underline underline-offset-2">
        back to the plant
      </Link>
    </div>
  );
}
