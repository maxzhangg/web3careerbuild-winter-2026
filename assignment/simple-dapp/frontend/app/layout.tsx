import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Simple Sepolia DApp",
  description: "Read and write message on Sepolia"
};

export default function RootLayout({
  children
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
