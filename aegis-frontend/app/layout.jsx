export const metadata = { title: 'AEGIS OMEGA X', description: 'Unified Security Intelligence Platform' }
export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body style={{ margin: 0, background: '#0a0a0f', color: '#e2e8f0', fontFamily: 'monospace' }}>
        {children}
      </body>
    </html>
  )
}
