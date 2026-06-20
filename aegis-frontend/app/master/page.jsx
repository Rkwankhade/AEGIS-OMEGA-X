'use client'
import Nav from '../components/Nav'
import StatusCard from '../components/StatusCard'
import { useApi } from '../components/useApi'

const PDT_URL     = process.env.NEXT_PUBLIC_PDT_API_URL       || 'http://localhost:8001'
const GENOME_URL  = process.env.NEXT_PUBLIC_GENOME_API_URL    || 'http://localhost:8002'
const KU_URL      = process.env.NEXT_PUBLIC_KNOWLEDGE_API_URL || 'http://localhost:8003'
const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL       || 'http://localhost:8000'

function Layer({ name, url, port }) {
  const { data, error, loading } = useApi(url + '/health', 8000)
  return <StatusCard
    title={name + ' :' + port}
    status={loading ? 'loading' : error ? 'error' : data?.status}
    detail={data?.version || data?.layer || ''}
  />
}

export default function Master() {
  const gw = useApi(GATEWAY_URL + '/health', 8000)
  return (
    <div>
      <Nav />
      <div style={{ padding:'32px 24px' }}>
        <h1 style={{ color:'#00d4ff', marginBottom:8 }}>AEGIS OMEGA X - Master Dashboard</h1>
        <p style={{ color:'#64748b', marginBottom:32 }}>Unified Security Intelligence Platform - 14-Layer Architecture</p>
        <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:32 }}>
          <Layer name="PDT"       url={PDT_URL}     port={8001} />
          <Layer name="Genome"    url={GENOME_URL}  port={8002} />
          <Layer name="Knowledge" url={KU_URL}      port={8003} />
          <Layer name="Gateway"   url={GATEWAY_URL} port={8000} />
        </div>
        <div style={{ background:'#0d1117', border:'1px solid #1e3a5f', borderRadius:8, padding:20 }}>
          <div style={{ color:'#64748b', fontSize:12, marginBottom:12 }}>GATEWAY RESPONSE</div>
          <pre style={{ color:'#94a3b8', fontSize:12, margin:0, whiteSpace:'pre-wrap' }}>
            {gw.loading ? 'Loading...' : gw.error ? gw.error : JSON.stringify(gw.data, null, 2)}
          </pre>
        </div>
        <div style={{ marginTop:24, display:'flex', gap:12, flexWrap:'wrap' }}>
          {[
            ['PDT API Docs', PDT_URL + '/docs'],
            ['Genome Docs',  GENOME_URL + '/docs'],
            ['KU Docs',      KU_URL + '/docs'],
            ['Gateway Docs', GATEWAY_URL + '/docs'],
          ].map(([label, href]) => (
            <a key={href} href={href} target="_blank" rel="noreferrer" style={{
              padding:'8px 14px', background:'#1e3a5f', borderRadius:6,
              color:'#00d4ff', textDecoration:'none', fontSize:13,
              border:'1px solid #00d4ff33'
            }}>{label}</a>
          ))}
        </div>
      </div>
    </div>
  )
}