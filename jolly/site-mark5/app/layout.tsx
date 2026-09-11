import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = { title: "MARK V | JIVO production", description: "The factory today. An agreed plan for tomorrow." };

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
