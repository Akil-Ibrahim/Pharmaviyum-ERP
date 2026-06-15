import { redirect } from "next/navigation";

// Redirect to sign-in for unauthenticated users
export default function Home() {
  redirect("/sign-in");
}
