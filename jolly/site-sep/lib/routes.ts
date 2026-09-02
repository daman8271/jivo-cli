// The site's route map — one place, imported by both the client Nav and
// server pages (a "use client" module can't export plain data to server code).
export const ROUTES: [string, string][] = [
  ["/", "Overview"],
  ["/days", "Day by day"],
  ["/lines", "Lines"],
  ["/storage", "Storage"],
  ["/materials", "Materials"],
  ["/order-by", "Order-by"],
  ["/build", "Build list"],
  ["/whatsapp", "WhatsApp"],
  ["/floor", "Floor 3D"],
];
