'use client'
import Nav from '../components/Nav'
import { useApi } from '../components/useApi'
export default function Genome() {
  const health = useApi('http://localhost:8002/health', 5000)
  const stats  = useApi('http://localhost:8002/genome/stats', 10000)
  return (
    <div>
      <Nav />
      <div style={{ padding:'32px 24px' }}>
        <h1 style={{ color:'#00d4ff', marginBottom:4 }}>🧬 Security Genome</h1>
        <p style={{ color:'#64748b', marginBottom:24 }}>MEGA-LAYER-2 · Port 8002</p>
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr', gap:16 }}>
          <div style={{ background:'#0d1117', border:'1px solid #1e3a5f', borderRadius:8, padding:20 }}>
            <div style={{ color:'#64748b', fontSize:12, marginBottom:8 }}>HEALTH</div>
            <pre style={{ color:'#94a3b8', fontSize:12, margin:0 }}>
              {health.loading ? 'Loading…' : health.error ? `❌ ${health.error}` : JSON.stringify(health.data, null, 2)}
            </pre>
          </div>
          <div style={{ background:'#0d1117', border:'1px solid #1e3a5f', borderRadius:8, padding:20 }}>
            <div style={{ color:'#64748b', fontSize:12, marginBottom:8 }}>STATS</div>
            <pre style={{ color:'#94a3b8', fontSize:12, margin:0 }}>
              {stats.loading ? 'Loading…' : stats.error ? `❌ ${stats.error}` : JSON.stringify(stats.data, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
