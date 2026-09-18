import "@/styles/globals.css";
import QueryProvider from "@/lib/query-provider";
import { AuthProvider } from "@/hooks/use-auth";
import { ToastProvider } from "@/components/ui/Toast";

export const metadata = {
  title: "MedRoute AI — Find the Right Doctor. Plan the Right Visit.",
  description:
    "MedRoute AI helps Medical Representatives discover doctors, medical shops and stockists across their territories from one intelligent platform.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <QueryProvider>
          <AuthProvider>
            <ToastProvider>{children}</ToastProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
