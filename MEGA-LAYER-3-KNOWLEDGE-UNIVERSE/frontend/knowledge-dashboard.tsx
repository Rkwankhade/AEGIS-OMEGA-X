// AEGIS OMEGA X — MEGA LAYER 3
// GLOBAL SECURITY KNOWLEDGE UNIVERSE — NEXT.JS DASHBOARD
// frontend/knowledge-dashboard.tsx

'use client';
import { useEffect, useState } from 'react';

const ACTORS = [
  { name:'APT29',   nation:'Russia',      score:0.97, techs:47, campaigns:8 },
  { name:'APT41',   nation:'China',       score:0.95, techs:62, campaigns:12 },
  { name:'Lazarus', nation:'N.Korea',     score:0.94, techs:55, campaigns:9 },
  { name:'APT33',   nation:'Iran',        score:0.88, techs:38, campaigns:6 },
  { name:'FIN7',    nation:'Unknown',     score:0.85, techs:41, campaigns:14 },
  { name:'APT28',   nation:'Russia',      score:0.91, techs:53, campaigns:11 },
  { name:'Sandworm',nation:'Russia',      score:0.93, techs:49, campaigns:7 },
];

const TOP_TECHNIQUES = [
  { id:'T1566', name:'Phishing',              prevalence:0.92, detections:284 },
  { id:'T1078', name:'Valid Accounts',        prevalence:0.81, detections:196 },
  { id:'T1059', name:'Command & Script',      prevalence:0.78, detections:321 },
  { id:'T1055', name:'Process Injection',     prevalence:0.71, detections:198 },
  { id:'T1486', name:'Data Encrypted',        prevalence:0.65, detections:142 },
  { id:'T1071', name:'App Layer Protocol',    prevalence:0.61, detections:167 },
  { id:'T1021', name:'Remote Services',       prevalence:0.58, detections:211 },
  { id:'T1003', name:'OS Credential Dumping', prevalence:0.55, detections:178 },
];

const KEV_CVES = [
  { id:'CVE-2024-3400', cvss:10.0, epss:0.971, product:'PAN-OS',       wild:true },
  { id:'CVE-2023-44487',cvss:7.5,  epss:0.953, product:'HTTP/2',       wild:true },
  { id:'CVE-2021-44228',cvss:10.0, epss:0.976, product:'Log4j',        wild:true },
  { id:'CVE-2023-23397',cvss:9.8,  epss:0.921, product:'Outlook',      wild:true },
  { id:'CVE-2024-1709', cvss:10.0, epss:0.968, product:'ConnectWise',  wild:true },
  { id:'CVE-2023-20198',cvss:10.0, epss:0.944, product:'IOS XE',       wild:true },
];

function ScoreBar({ score, color='#00FF9C' }: { score:number; color?:string }) {
  return (
    <div style={{ display:'flex', alignItems:'center', gap:'8px' }}>
      <div style={{ flex:1, height:'4px', background:'#1a1a3e', borderRadius:'2px' }}>
        <div style={{
          height:'100%', width:`${score*100}%`,
          background: color, borderRadius:'2px',
          boxShadow:`0 0 6px ${color}66`,
          transition:'width 0.5s ease',
        }} />
      </div>
      <span style={{ fontSize:'10px', color, fontFamily:'monospace', minWidth:'32px' }}>
        {(score*100).toFixed(0)}%
      </span>
    </div>
  );
}

function KnowledgeCounter({ label, value, color }: { label:string; value:string; color:string }) {
  return (
    <div style={{
      background:'#0a0a1a', border:`1px solid ${color}22`,
      borderRadius:'8px', padding:'14px 16px', position:'relative', overflow:'hidden',
    }}>
      <div style={{
        position:'absolute', top:0, left:0, right:0, height:'2px',
        background:color, boxShadow:`0 0 10px ${color}`,
      }} />
      <div style={{ fontSize:'10px', color:'#666', letterSpacing:'0.1em', marginBottom:'6px' }}>
        {label}
      </div>
      <div style={{ fontSize:'22px', fontWeight:700, color, fontFamily:'monospace' }}>
        {value}
      </div>
    </div>
  );
}

export default function KnowledgeDashboard() {
  const [ticker, setTicker] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [universeStats, setUniverseStats] = useState({
    nodes: 12_400_000, edges: 94_200_000, actors:847,
    techniques:714, cves:247_891, rules:18_432,
    iocs:4_200_000, incidents:28_441,
  });

  useEffect(() => {
    const i = setInterval(() => {
      setTicker(t => t+1);
      setUniverseStats(prev => ({
        ...prev,
        nodes: prev.nodes + Math.floor(Math.random()*50),
        edges: prev.edges + Math.floor(Math.random()*200),
        iocs:  prev.iocs  + Math.floor(Math.random()*100),
      }));
    }, 2000);
    return () => clearInterval(i);
  }, []);

  const handleSearch = () => {
    if (!searchQuery.trim()) return;
    const types = ['technique','cve','threat_actor','detection_rule','malware','incident'];
    setSearchResults(Array.from({ length:8 }, (_, i) => ({
      id:    `node-${i}`,
      type:  types[Math.floor(Math.random()*types.length)],
      name:  `${searchQuery} — Result ${i+1}`,
      score: Math.round((0.97 - i*0.08)*100)/100,
      desc:  `Knowledge node matching "${searchQuery}" with semantic similarity.`,
    })));
  };

  const typeColor: Record<string,string> = {
    technique:'#3D9CFF', cve:'#FF3D3D', threat_actor:'#FF8C00',
    detection_rule:'#00FF9C', malware:'#8B5CF6', incident:'#FFB800',
  };

  return (
    <div style={{ minHeight:'100vh', background:'#050510', color:'#e0e0ff',
      fontFamily:'system-ui, monospace' }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        * { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar { width:4px; }
        ::-webkit-scrollbar-thumb { background:#1a1a4e; }
        input:focus { outline:none; }
      `}</style>

      {/* HEADER */}
      <div style={{
        background:'#080820', borderBottom:'1px solid #1a1a4e',
        padding:'12px 24px', display:'flex', alignItems:'center',
        justifyContent:'space-between', position:'sticky', top:0, zIndex:100,
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:'16px' }}>
          <div style={{
            width:'32px', height:'32px',
            background:'linear-gradient(135deg, #8B5CF6, #3D9CFF)',
            borderRadius:'6px', display:'flex', alignItems:'center',
            justifyContent:'center', fontSize:'18px',
          }}>🌐</div>
          <div>
            <div style={{ fontSize:'13px', fontWeight:700, letterSpacing:'0.15em', color:'#fff' }}>
              AEGIS OMEGA X
            </div>
            <div style={{ fontSize:'10px', color:'#555', letterSpacing:'0.1em' }}>
              MEGA LAYER 3 · GLOBAL SECURITY KNOWLEDGE UNIVERSE
            </div>
          </div>
        </div>
        <div style={{ display:'flex', gap:'24px', alignItems:'center' }}>
          {[
            { l:'KNOWLEDGE NODES', v: (universeStats.nodes/1_000_000).toFixed(2)+'M', c:'#8B5CF6' },
            { l:'RELATIONSHIPS',   v: (universeStats.edges/1_000_000).toFixed(1)+'M',  c:'#3D9CFF' },
            { l:'THREAT ACTORS',   v: universeStats.actors,                            c:'#FF8C00' },
            { l:'CVEs TRACKED',    v: universeStats.cves.toLocaleString(),             c:'#FF3D3D' },
          ].map((s,i) => (
            <div key={i} style={{ textAlign:'center' }}>
              <div style={{ fontSize:'10px', color:'#555' }}>{s.l}</div>
              <div style={{ fontSize:'16px', fontWeight:700, color:s.c, fontFamily:'monospace' }}>
                {s.v}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding:'20px 24px', maxWidth:'1600px', margin:'0 auto' }}>

        {/* UNIVERSE COUNTERS */}
        <div style={{ display:'grid', gridTemplateColumns:'repeat(8,1fr)', gap:'10px', marginBottom:'20px' }}>
          {[
            { label:'TECHNIQUES',   value: universeStats.techniques.toLocaleString(), color:'#3D9CFF' },
            { label:'CVEs',         value: universeStats.cves.toLocaleString(),       color:'#FF3D3D' },
            { label:'THREAT ACTORS',value: universeStats.actors.toString(),           color:'#FF8C00' },
            { label:'DETECT RULES', value: universeStats.rules.toLocaleString(),      color:'#00FF9C' },
            { label:'IOCs',         value: (universeStats.iocs/1_000_000).toFixed(2)+'M', color:'#FFB800' },
            { label:'INCIDENTS',    value: universeStats.incidents.toLocaleString(),  color:'#8B5CF6' },
            { label:'FRAMEWORKS',   value: '34',                                      color:'#00D4FF' },
            { label:'SIGMA RULES',  value: '17,842',                                  color:'#00FF9C' },
          ].map((s,i) => <KnowledgeCounter key={i} {...s} />)}
        </div>

        {/* SEMANTIC SEARCH */}
        <div style={{
          background:'#0a0a1a', border:'1px solid #8B5CF644',
          borderRadius:'8px', padding:'20px', marginBottom:'20px',
        }}>
          <div style={{ fontSize:'11px', color:'#888', letterSpacing:'0.1em',
            fontWeight:700, marginBottom:'12px' }}>
            SEMANTIC KNOWLEDGE SEARCH
          </div>
          <div style={{ display:'flex', gap:'12px', marginBottom:'16px' }}>
            <input
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSearch()}
              placeholder="Search: 'phishing techniques used by APT29' or 'CVEs affecting Log4j'..."
              style={{
                flex:1, background:'#050510', border:'1px solid #8B5CF644',
                borderRadius:'6px', padding:'10px 14px', color:'#e0e0ff',
                fontSize:'13px', fontFamily:'monospace',
              }}
            />
            <button onClick={handleSearch} style={{
              background:'linear-gradient(135deg,#8B5CF6,#3D9CFF)',
              border:'none', borderRadius:'6px', padding:'10px 24px',
              color:'#fff', fontWeight:700, cursor:'pointer', fontSize:'12px',
              letterSpacing:'0.1em',
            }}>
              SEARCH
            </button>
          </div>
          {searchResults.length > 0 && (
            <div style={{ display:'grid', gridTemplateColumns:'repeat(2,1fr)', gap:'8px' }}>
              {searchResults.map((r,i) => (
                <div key={i} style={{
                  background:'#080818', border:`1px solid ${typeColor[r.type]||'#333'}33`,
                  borderRadius:'6px', padding:'12px',
                  borderLeft:`3px solid ${typeColor[r.type]||'#666'}`,
                }}>
                  <div style={{ display:'flex', justifyContent:'space-between', marginBottom:'4px' }}>
                    <span style={{ fontSize:'10px', color: typeColor[r.type]||'#888',
                      fontWeight:700, letterSpacing:'0.08em' }}>
                      {r.type.toUpperCase().replace('_',' ')}
                    </span>
                    <span style={{ fontSize:'10px', color:'#00FF9C', fontFamily:'monospace' }}>
                      {(r.score*100).toFixed(0)}% match
                    </span>
                  </div>
                  <div style={{ fontSize:'12px', color:'#ddd', fontWeight:600, marginBottom:'3px' }}>
                    {r.name}
                  </div>
                  <div style={{ fontSize:'11px', color:'#555' }}>{r.desc}</div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* MAIN GRID */}
        <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:'20px', marginBottom:'20px' }}>

          {/* THREAT ACTORS */}
          <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e',
            borderRadius:'8px', padding:'20px' }}>
            <div style={{ fontSize:'11px', color:'#888', letterSpacing:'0.1em',
              fontWeight:700, marginBottom:'14px' }}>
              TOP THREAT ACTORS — THREAT SCORE
            </div>
            {ACTORS.map((a,i) => (
              <div key={i} style={{ marginBottom:'12px' }}>
                <div style={{ display:'flex', justifyContent:'space-between',
                  fontSize:'12px', marginBottom:'5px' }}>
                  <div>
                    <span style={{ color:'#fff', fontWeight:600 }}>{a.name}</span>
                    <span style={{ color:'#555', marginLeft:'8px', fontSize:'10px' }}>
                      {a.nation}
                    </span>
                  </div>
                  <div style={{ color:'#888', fontSize:'10px', fontFamily:'monospace' }}>
                    {a.techs}T · {a.campaigns}C
                  </div>
                </div>
                <ScoreBar score={a.score}
                  color={a.score>0.93?'#FF3D3D':a.score>0.88?'#FF8C00':'#FFB800'} />
              </div>
            ))}
          </div>

          {/* TOP TECHNIQUES */}
          <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e',
            borderRadius:'8px', padding:'20px' }}>
            <div style={{ fontSize:'11px', color:'#888', letterSpacing:'0.1em',
              fontWeight:700, marginBottom:'14px' }}>
              TOP ATT&CK TECHNIQUES — PREVALENCE
            </div>
            {TOP_TECHNIQUES.map((t,i) => (
              <div key={i} style={{ marginBottom:'11px' }}>
                <div style={{ display:'flex', justifyContent:'space-between',
                  fontSize:'12px', marginBottom:'5px' }}>
                  <div>
                    <span style={{ color:'#3D9CFF', fontFamily:'monospace',
                      fontSize:'10px', marginRight:'6px' }}>{t.id}</span>
                    <span style={{ color:'#ccc' }}>{t.name}</span>
                  </div>
                  <span style={{ color:'#555', fontSize:'10px' }}>
                    {t.detections} rules
                  </span>
                </div>
                <ScoreBar score={t.prevalence} color='#3D9CFF' />
              </div>
            ))}
          </div>

          {/* CISA KEV */}
          <div style={{ background:'#0a0a1a', border:'1px solid #FF3D3D22',
            borderRadius:'8px', padding:'20px' }}>
            <div style={{ fontSize:'11px', color:'#888', letterSpacing:'0.1em',
              fontWeight:700, marginBottom:'14px',
              display:'flex', alignItems:'center', gap:'8px' }}>
              <span style={{
                width:'8px', height:'8px', borderRadius:'50%',
                background:'#FF3D3D', display:'inline-block',
                animation:'pulse 1s infinite',
              }} />
              CISA KEV — ACTIVELY EXPLOITED
            </div>
            {KEV_CVES.map((c,i) => (
              <div key={i} style={{
                padding:'8px 0', borderBottom:'1px solid #0f0f2a',
              }}>
                <div style={{ display:'flex', justifyContent:'space-between',
                  alignItems:'center', marginBottom:'4px' }}>
                  <span style={{ color:'#FF3D3D', fontFamily:'monospace',
                    fontSize:'11px', fontWeight:700 }}>{c.id}</span>
                  <span style={{
                    background:'#FF3D3D22', color:'#FF3D3D',
                    padding:'1px 6px', borderRadius:'3px',
                    fontSize:'9px', fontWeight:700,
                  }}>EXPLOITED</span>
                </div>
                <div style={{ display:'flex', justifyContent:'space-between',
                  fontSize:'10px', color:'#666' }}>
                  <span>{c.product}</span>
                  <span style={{ color:'#FFB800' }}>CVSS {c.cvss}</span>
                  <span style={{ color:'#FF8C00' }}>EPSS {(c.epss*100).toFixed(1)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* KNOWLEDGE GRAPH STATS */}
        <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e',
          borderRadius:'8px', padding:'20px' }}>
          <div style={{ fontSize:'11px', color:'#888', letterSpacing:'0.1em',
            fontWeight:700, marginBottom:'16px' }}>
            KNOWLEDGE GRAPH — RELATIONSHIP DENSITY
          </div>
          <div style={{ display:'grid', gridTemplateColumns:'repeat(6,1fr)', gap:'16px' }}>
            {[
              { label:'Actor → Technique',  count:'48,291',  pct:0.82 },
              { label:'Technique → CVE',    count:'12,847',  pct:0.61 },
              { label:'Rule → Technique',   count:'89,441',  pct:0.94 },
              { label:'Malware → Technique',count:'31,208',  pct:0.73 },
              { label:'CVE → CWE',          count:'198,420', pct:0.88 },
              { label:'Control → Technique',count:'27,841',  pct:0.67 },
            ].map((rel,i) => (
              <div key={i}>
                <div style={{ fontSize:'10px', color:'#888', marginBottom:'6px' }}>
                  {rel.label}
                </div>
                <div style={{ fontSize:'16px', color:'#8B5CF6',
                  fontFamily:'monospace', fontWeight:700, marginBottom:'6px' }}>
                  {rel.count}
                </div>
                <ScoreBar score={rel.pct} color='#8B5CF6' />
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
