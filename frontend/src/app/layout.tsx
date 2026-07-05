import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Confoundr | Causal Validity Platform',
  description: 'AI-powered causal validity checks for your datasets.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>
        <nav style={{ padding: '24px', borderBottom: '1px solid var(--border-color)', background: 'var(--bg-card)' }}>
          <div className="container" style={{ padding: '0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <a href="/" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'linear-gradient(135deg, var(--primary), var(--secondary))', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold' }}>C</div>
              <span style={{ fontFamily: 'Outfit', fontSize: '1.5rem', fontWeight: 600 }}>Confoundr</span>
            </a>
            <div style={{ display: 'flex', gap: '24px' }}>
              <a href="/" style={{ color: 'var(--text-muted)', transition: 'color 0.2s' }} onMouseOver={(e) => e.currentTarget.style.color = 'var(--text-main)'} onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}>Dashboard</a>
              <a href={process.env.NEXT_PUBLIC_API_URL + '/metrics'} target="_blank" rel="noreferrer" style={{ color: 'var(--text-muted)', transition: 'color 0.2s' }} onMouseOver={(e) => e.currentTarget.style.color = 'var(--text-main)'} onMouseOut={(e) => e.currentTarget.style.color = 'var(--text-muted)'}>Metrics</a>
            </div>
          </div>
        </nav>
        <main>
          {children}
        </main>
      </body>
    </html>
  )
}
