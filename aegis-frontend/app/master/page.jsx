'use client'
import Nav from '../components/Nav'
import StatusCard from '../components/StatusCard'
import { useApi } from '../components/useApi'

function Layer({ name, url, port }) {
  const { data, error, loading } = useApi(`${url}/health`, 8000)
  return <StatusCard
    title={`${name} :${port}`}
    status={loading ? 'loading' : error ? 'error' : data?.status}
    detail={data?.version || data?.layer || ''}
  />
}

export default function Master() {
  const gw = useApi('http://localhost:8000/health', 8000)
  return (
    <div>
      <Nav />
      <div style={{ padding:'32px 24px' }}>
        <h1 style={{ color:'#00d4ff', marginBottom:8 }}>AEGIS OMEGA X — Master Dashboard</h1>
        <p style={{ color:'#64748b', marginBottom:32 }}>Unified Security Intelligence Platform · 14-Layer Architecture</p>
        <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:32 }}>
          <Layer name="PDT"       url="http://localhost:8001" port={8001} />
          <Layer name="Genome"    url="http://localhost:8002" port={8002} />
          <Layer name="Knowledge" url="http://localhost:8003" port={8003} />
          <Layer name="Gateway"   url="http://localhost:8000" port={8000} />
        </div>
        <div style={{ background:'#0d1117', border:'1px solid #1e3a5f', borderRadius:8, padding:20 }}>
          <div style={{ color:'#64748b', fontSize:12, marginBottom:12 }}>GATEWAY RESPONSE</div>
          <pre style={{ color:'#94a3b8', fontSize:12, margin:0, whiteSpace:'pre-wrap' }}>
            {gw.loading ? 'Loading…' : gw.error ? gw.error : JSON.stringify(gw.data, null, 2)}
          </pre>
        </div>
        <div style={{ marginTop:24, display:'flex', gap:12, flexWrap:'wrap' }}>
          {[
            ['Grafana',      'http://localhost:3000'],
            ['PDT API Docs', 'http://localhost:8001/docs'],
            ['Genome Docs',  'http://localhost:8002/docs'],
            ['KU Docs',      'http://localhost:8003/docs'],
            ['Gateway Docs', 'http://localhost:8000/docs'],
            ['Kafka UI',     'http://localhost:8080'],
          ].map(([label, href]) => (
            <a key={href} href={href} target="_blank" rel="noreferrer" style={{
              padding:'8px 14px', background:'#1e3a5f', borderRadius:6,
              color:'#00d4ff', textDecoration:'none', fontSize:13,
              border:'1px solid #00d4ff33'
            }}>{label} ↗</a>
          ))}
        </div>
      </div>
    </div>
  )
}
