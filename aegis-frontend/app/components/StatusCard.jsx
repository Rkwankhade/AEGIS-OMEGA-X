export default function StatusCard({ title, status, detail, color='#00d4ff' }) {
  const ok = status === 'operational' || status === 'ok'
  return (
    <div style={{ background:'#0d1117', border:`1px solid ${ok?'#1e3a5f':'#5f1e1e'}`, borderRadius:8, padding:'16px 20px', minWidth:200 }}>
      <div style={{ fontSize:11, color:'#64748b', marginBottom:4 }}>{title}</div>
      <div style={{ color: ok?color:'#f87171', fontWeight:'bold', fontSize:15 }}>
        {ok ? '● OPERATIONAL' : '● DEGRADED'}
      </div>
      {detail && <div style={{ fontSize:12, color:'#94a3b8', marginTop:6 }}>{detail}</div>}
    </div>
  )
}
