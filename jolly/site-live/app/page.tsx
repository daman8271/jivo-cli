import OverviewClient from "../components/OverviewClient";

// No data at build time, by design: this file renders a shell and the client
// fetches every figure in it from the publisher.
export default function Page() {
  return <OverviewClient />;
}
