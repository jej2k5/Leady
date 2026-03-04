import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Leady",
  description: "Lead discovery and qualification workspace",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
