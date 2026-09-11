// The site's route map — one place, imported by both the client Nav and
// server pages (a "use client" module can't export plain data to server code).
// Labels are floor words (PLAIN-LANGUAGE.md swap list). The URLs never change.
export const ROUTES: [string, string][] = [
  ["/", "Summary"],
  ["/days", "Day by day"],
  ["/lines", "Machines"],
  ["/storage", "Godown"],
  ["/materials", "Stock"],
  ["/order-by", "Order by when"],
  ["/build", "Run list"],
  ["/whatsapp", "Messages (not sent)"],
  ["/floor", "Floor map"],
];
