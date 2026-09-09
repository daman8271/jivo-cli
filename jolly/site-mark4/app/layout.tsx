import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "JIVO Mark IV · Production planner",
  description:
    "A line-by-line production plan grounded in machine rules, available materials and factory records.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script
          dangerouslySetInnerHTML={{
            __html: `(function(){var theme;try{theme=localStorage.getItem('jivo-mark4-theme')}catch(e){}if(theme!=='dark'&&theme!=='light')theme=window.matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';document.documentElement.dataset.theme=theme})()`,
          }}
        />
      </head>
      <body>{children}</body>
    </html>
  );
}
