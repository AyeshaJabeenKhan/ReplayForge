import "./globals.css";

export const metadata = {
  title: "ReplayForge",
  description: "Conversation replay and regression testing for LLM upgrades",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
