// MAINTENANCE GATE
// Everyone sees the maintenance page while maintenance.json says { "on": true }.
// One laptop does not: visiting /?pass=<the token in maintenance.json> drops a cookie
// that lets that browser through from then on. The cookie is httpOnly and lasts 30 days.
// Nothing here touches the plan itself — it only decides which page a visitor is served.
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
import maintenance from "./maintenance.json";

const COOKIE = "jivo-pass";

export default function proxy(req: NextRequest) {
  if (!maintenance.on) return NextResponse.next();

  const url = req.nextUrl;

  // the magic link: set the cookie once, then land on the real page
  const given = url.searchParams.get("pass");
  if (given && given === maintenance.pass) {
    const clean = new URL(url);
    clean.searchParams.delete("pass");
    const res = NextResponse.redirect(clean);
    res.cookies.set(COOKIE, maintenance.pass, {
      httpOnly: true,
      sameSite: "lax",
      secure: true,
      maxAge: 60 * 60 * 24 * 30,
      path: "/",
    });
    return res;
  }

  // already let through on this browser
  if (req.cookies.get(COOKIE)?.value === maintenance.pass) return NextResponse.next();

  // everyone else: show the maintenance page at whatever address they asked for
  if (url.pathname === "/maintenance") return NextResponse.next();
  const res = NextResponse.rewrite(new URL("/maintenance", req.url));
  res.headers.set("x-robots-tag", "noindex");
  return res;
}

// let the page's own styles, fonts and icons through, or the maintenance page arrives naked
export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico|icon.png|apple-icon.png).*)"],
};
