'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
const links = [
  { href: '/master',    label: '⚡ Master' },
  { href: '/pdt',       label: '🌍 PDT' },
  { href: '/genome',    label: '🧬 Genome' },
  { href: '/knowledge', label: '🧠 Knowledge' },
]
export default function Nav() {
  const path = usePathname()
  return (
    <nav style={{ display:'flex', gap:8, padding:'12px 24px', background:'#0d1117', borderBottom:'1px solid #1e3a5f' }}>
      <span style={{ color:'#00d4ff', fontWeight:'bold', marginRight:16 }}>AEGIS OMEGA X</span>
      {links.map(l => (
        <Link key={l.href} href={l.href} style={{
          padding:'6px 14px', borderRadius:6, textDecoration:'none', fontSize:13,
          background: path===l.href ? '#1e3a5f' : 'transparent',
          color: path===l.href ? '#00d4ff' : '#94a3b8',
          border: path===l.href ? '1px solid #00d4ff44' : '1px solid transparent',
        }}>{l.label}</Link>
      ))}
    </nav>
  )
}
