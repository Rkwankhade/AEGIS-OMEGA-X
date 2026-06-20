// AEGIS OMEGA X — UNIFIED MASTER DASHBOARD
// All 14 Mega Layers in one interface
// frontend/master-dashboard.tsx

'use client';
import { useEffect, useState, useRef } from 'react';

// ──────────────────────────────────────────────
// TYPES
// ──────────────────────────────────────────────
interface LayerStatus {
  id: number; name: string; shortName: string;
  status: 'operational'|'degraded'|'offline';
  health: number; color: string; port: number;
  metrics: Record<string, string|number>;
}

interface SOCAlert { id: string; title: string; severity: string; time: string; source: string; }
interface ForecastPoint { day: number; risk: number; lower: number; upper: number; }
interface AgentStatus { id: string; name: string; cls: string; status: string; tasks: number; trust: number; }
interface CPSSystem { name: string; type: string; cyberRisk: number; physRisk: number; resilience: number; }
interface QuantumItem { algorithm: string; vulnerable: boolean; pqc: string; priority: string; }
interface EconControl { control: string; roi: number; cost: number; selected: boolean; }

// ──────────────────────────────────────────────
// LAYER REGISTRY
// ──────────────────────────────────────────────
const LAYERS: LayerStatus[] = [
  { id:1,  name:'Planetary Digital Twin',       shortName:'PDT',        status:'operational', health:0.97, color:'#00FF9C', port:8001, metrics:{'Entities':'10,247','Assets':'1.28M','Risk':'34.7%'} },
  { id:2,  name:'Enterprise Security Genome',   shortName:'GENOME',     status:'operational', health:0.94, color:'#FF8C00', port:8002, metrics:{'Nodes':'4,891','Mutations/hr':'67','Resilience':'76%'} },
  { id:3,  name:'Global Knowledge Universe',    shortName:'KU',         status:'operational', health:0.98, color:'#8B5CF6', port:8003, metrics:{'KNodes':'12.4M','CVEs':'247K','Rules':'18.4K'} },
  { id:4,  name:'AI Security Civilization',     shortName:'AI-CIV',     status:'operational', health:0.92, color:'#3D9CFF', port:8004, metrics:{'Agents':'30','Tasks/hr':'847','Trust':'0.84'} },
  { id:5,  name:'Autonomous SOC Ecosystem',     shortName:'SOC',        status:'operational', health:0.96, color:'#FF3D3D', port:8005, metrics:{'Alerts':'1,284','MTTR':'18min','FP Rate':'4.2%'} },
  { id:6,  name:'Predictive Cyber Intelligence',shortName:'PREDICT',    status:'operational', health:0.91, color:'#FFB800', port:8006, metrics:{'Forecasts':'482','Horizon':'20yr','Accuracy':'89%'} },
  { id:7,  name:'Architecture Evolution',       shortName:'ARCH',       status:'operational', health:0.89, color:'#00D4FF', port:8007, metrics:{'Blueprints':'4','Best Score':'0.74','Roadmaps':'48'} },
  { id:8,  name:'Security Economics Engine',    shortName:'ECON',       status:'operational', health:0.95, color:'#00FF9C', port:8008, metrics:{'Portfolio ROI':'3.2x','Risk Δ':'-42%','Budget':'$2M'} },
  { id:9,  name:'Autonomous Governance',        shortName:'GOV',        status:'operational', health:0.93, color:'#FF8C00', port:8009, metrics:{'Policies':'47','Compliance':'81%','Frameworks':'6'} },
  { id:10, name:'Digital Society Simulator',    shortName:'SIM',        status:'operational', health:0.97, color:'#8B5CF6', port:8010, metrics:{'Orgs':'100','Incidents/yr':'28','Avg Maturity':'0.48'} },
  { id:11, name:'Foundation Model Ecosystem',   shortName:'FM',         status:'operational', health:0.99, color:'#3D9CFF', port:8011, metrics:{'Models':'7','Params':'191B','Accuracy':'91%'} },
  { id:12, name:'Formal Verification',          shortName:'VERIFY',     status:'operational', health:0.88, color:'#FF3D3D', port:8012, metrics:{'Properties':'4','Verified':'3','Tools':'TLA+/Alloy/Coq'} },
  { id:13, name:'Quantum-Safe Enterprise',      shortName:'QSE',        status:'operational', health:0.94, color:'#FFB800', port:8013, metrics:{'Vulnerable Algos':'847','Migration':'34%','PQC Ready':'12%'} },
  { id:14, name:'Cyber-Physical Resilience',    shortName:'CPR',        status:'operational', health:0.91, color:'#00D4FF', port:8014, metrics:{'CPS':'48','OT Risk':'71%','Safety':'0.89'} },
];

// ──────────────────────────────────────────────
// MOCK DATA GENERATORS
// ──────────────────────────────────────────────
const mkAlerts = (): SOCAlert[] => [
  { id:'AX-9841', title:'CRYSTALS-Kyber exploit attempt — payment-api', severity:'critical', time:'00:02', source:'EDR' },
  { id:'AX-9842', title:'APT29 lateral movement detected — corp-net',   severity:'critical', time:'00:05', source:'SIEM' },
  { id:'AX-9843', title:'Privilege escalation — svc-payment → admin',   severity:'high',     time:'00:08', source:'IAM' },
  { id:'AX-9844', title:'Anomalous Modbus traffic — plant-floor-3',      severity:'high',     time:'00:11', source:'OT-IDS' },
  { id:'AX-9845', title:'Mass credential stuffing — auth-api',           severity:'medium',   time:'00:14', source:'WAF' },
  { id:'AX-9846', title:'SHA-1 detected in TLS handshake — vendor VPN',  severity:'medium',   time:'00:19', source:'Scanner' },
  { id:'AX-9847', title:'Sigma rule fired: T1566.001 attachment',        severity:'high',     time:'00:22', source:'Email GW' },
  { id:'AX-9848', title:'Unusual data staging — finance-server-02',      severity:'medium',   time:'00:27', source:'DLP' },
];

const mkForecast = (): ForecastPoint[] =>
  Array.from({ length: 50 }, (_, i) => {
    const risk = 0.42 + i * 0.003 + Math.sin(i * 0.3) * 0.04;
    return { day: i * 7, risk: +risk.toFixed(3), lower: +(risk-0.06).toFixed(3), upper: +(risk+0.08).toFixed(3) };
  });

const mkAgents = (): AgentStatus[] => [
  { id:'analyst-001',      name:'Analyst Agent 1',     cls:'analyst',      status:'working',    tasks:142, trust:0.91 },
  { id:'detection-001',    name:'Detection Agent 1',   cls:'detection',    status:'working',    tasks:289, trust:0.94 },
  { id:'intelligence-001', name:'Intel Agent 1',       cls:'intelligence', status:'idle',       tasks:87,  trust:0.88 },
  { id:'risk-001',         name:'Risk Agent 1',        cls:'risk',         status:'working',    tasks:203, trust:0.92 },
  { id:'governance-001',   name:'Governance Agent 1',  cls:'governance',   status:'working',    tasks:64,  trust:0.89 },
  { id:'architect-001',    name:'Architect Agent 1',   cls:'architect',    status:'idle',       tasks:31,  trust:0.87 },
  { id:'optimization-001', name:'Optim Agent 1',       cls:'optimization', status:'working',    tasks:118, trust:0.90 },
  { id:'compliance-001',   name:'Compliance Agent 1',  cls:'compliance',   status:'delegating', tasks:72,  trust:0.86 },
  { id:'audit-001',        name:'Audit Agent 1',       cls:'audit',        status:'idle',       tasks:44,  trust:0.93 },
  { id:'research-001',     name:'Research Agent 1',    cls:'research',     status:'working',    tasks:28,  trust:0.85 },
];

const mkCPS = (): CPSSystem[] => [
  { name:'PowerGrid-East',  type:'energy_grid',    cyberRisk:0.71, physRisk:0.52, resilience:0.61 },
  { name:'SmartFactory-01', type:'manufacturing',  cyberRisk:0.63, physRisk:0.41, resilience:0.68 },
  { name:'WaterTreatment-N',type:'water',          cyberRisk:0.78, physRisk:0.58, resilience:0.54 },
  { name:'Rail-Control-Sys',type:'transport',      cyberRisk:0.67, physRisk:0.44, resilience:0.66 },
  { name:'BuildingMgmt-HQ', type:'building',       cyberRisk:0.44, physRisk:0.21, resilience:0.82 },
];

const mkQuantum = (): QuantumItem[] => [
  { algorithm:'RSA-2048',   vulnerable:true,  pqc:'CRYSTALS-Kyber-768',  priority:'critical' },
  { algorithm:'ECDSA-P256', vulnerable:true,  pqc:'Dilithium3',           priority:'critical' },
  { algorithm:'DH-2048',    vulnerable:true,  pqc:'CRYSTALS-Kyber-768',  priority:'critical' },
  { algorithm:'AES-256',    vulnerable:false, pqc:'—',                    priority:'none' },
  { algorithm:'SHA-256',    vulnerable:false, pqc:'—',                    priority:'none' },
  { algorithm:'DSA-2048',   vulnerable:true,  pqc:'Dilithium3',           priority:'high' },
  { algorithm:'RSA-4096',   vulnerable:true,  pqc:'CRYSTALS-Kyber-1024', priority:'high' },
  { algorithm:'ChaCha20',   vulnerable:false, pqc:'—',                    priority:'none' },
];

const mkEconControls = (): EconControl[] => [
  { control:'Security Awareness', roi:5.0, cost:30_000,  selected:true  },
  { control:'MFA',                roi:4.2, cost:50_000,  selected:true  },
  { control:'PAM',                roi:3.8, cost:150_000, selected:true  },
  { control:'Vuln Mgmt',         roi:3.5, cost:80_000,  selected:true  },
  { control:'EDR',                roi:3.1, cost:120_000, selected:true  },
  { control:'Zero Trust',         roi:2.8, cost:300_000, selected:true  },
  { control:'Threat Intel',       roi:2.9, cost:90_000,  selected:true  },
  { control:'SIEM',               roi:2.4, cost:200_000, selected:false },
  { control:'AI SOC',             roi:2.5, cost:400_000, selected:false },
];

// ──────────────────────────────────────────────
// SMALL COMPONENTS
// ──────────────────────────────────────────────
const SEV_COLOR: Record<string,string> = {
  critical:'#FF3D3D', high:'#FF8C00', medium:'#FFB800', low:'#00FF9C'
};
const STATUS_COLOR: Record<string,string> = {
  working:'#00FF9C', idle:'#3D9CFF', delegating:'#FFB800', failed:'#FF3D3D'
};
const PRIO_COLOR: Record<string,string> = {
  critical:'#FF3D3D', high:'#FF8C00', medium:'#FFB800', none:'#00FF9C'
};

function MiniBar({ value, max=1, color='#00FF9C', height=4 }:
  { value:number; max?:number; color?:string; height?:number }) {
  return (
    <div style={{ height, background:'#1a1a3e', borderRadius:2, overflow:'hidden' }}>
      <div style={{
        height:'100%', width:`${(value/max)*100}%`,
        background:color, borderRadius:2,
        boxShadow:`0 0 6px ${color}66`,
        transition:'width 0.5s ease',
      }} />
    </div>
  );
}

function Pulse({ color='#FF3D3D' }: { color?:string }) {
  return (
    <span style={{
      display:'inline-block', width:8, height:8, borderRadius:'50%',
      background:color, animation:'pulse 1s infinite',
    }} />
  );
}

// ──────────────────────────────────────────────
// MAIN DASHBOARD
// ──────────────────────────────────────────────
export default function MasterDashboard() {
  const [activeLayer, setActiveLayer] = useState(1);
  const [tick, setTick] = useState(0);
  const [layers, setLayers] = useState(LAYERS);
  const [alerts] = useState(mkAlerts());
  const [forecast] = useState(mkForecast());
  const [agents] = useState(mkAgents());
  const [cps] = useState(mkCPS());
  const [quantum] = useState(mkQuantum());
  const [econ] = useState(mkEconControls());
  const [globalRisk, setGlobalRisk] = useState(0.412);
  const [currentTime, setCurrentTime] = useState('');

  useEffect(() => {
    const i = setInterval(() => {
      setTick(t => t + 1);
      setGlobalRisk(r => Math.max(0.1, Math.min(0.95, r + (Math.random()-0.48)*0.008)));
      setLayers(prev => prev.map(l => ({
        ...l, health: Math.max(0.7, Math.min(1.0, l.health + (Math.random()-0.48)*0.005))
      })));
      setCurrentTime(new Date().toISOString().replace('T',' ').slice(0,19) + ' UTC');
    }, 1500);
    return () => clearInterval(i);
  }, []);

  const riskColor = globalRisk > 0.7 ? '#FF3D3D' : globalRisk > 0.4 ? '#FFB800' : '#00FF9C';
  const active = layers.find(l => l.id === activeLayer)!;
  const critAlerts = alerts.filter(a => a.severity === 'critical').length;

  // Forecast SVG path
  const fWidth = 560; const fHeight = 80;
  const fPoints = forecast.map((p, i) => ({
    x: (i / (forecast.length-1)) * fWidth,
    y: fHeight - p.risk * fHeight,
  }));
  const fPath = fPoints.map((p,i) => `${i===0?'M':'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
  const upperPoints = forecast.map((p,i) => ({
    x:(i/(forecast.length-1))*fWidth, y:fHeight-p.upper*fHeight
  }));
  const lowerPoints = [...forecast.map((p,i) => ({
    x:(i/(forecast.length-1))*fWidth, y:fHeight-p.lower*fHeight
  }))].reverse();
  const bandPath = [
    ...upperPoints.map((p,i)=>`${i===0?'M':'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`),
    ...lowerPoints.map(p=>`L${p.x.toFixed(1)},${p.y.toFixed(1)}`),
    'Z'
  ].join(' ');

  return (
    <div style={{ minHeight:'100vh', background:'#050510', color:'#e0e0ff',
      fontFamily:'system-ui, monospace', display:'flex', flexDirection:'column' }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:0.4;transform:scale(0.8)} }
        @keyframes fadeIn { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
        * { box-sizing:border-box; margin:0; padding:0; }
        ::-webkit-scrollbar { width:3px; } ::-webkit-scrollbar-thumb { background:#1a1a4e; }
        button { cursor:pointer; } button:focus { outline:none; }
      `}</style>

      {/* ── TOP HEADER ───────────────────────── */}
      <div style={{
        background:'#080820', borderBottom:'1px solid #1a1a4e',
        padding:'10px 20px', display:'flex', alignItems:'center',
        justifyContent:'space-between', position:'sticky', top:0, zIndex:200, gap:16,
      }}>
        <div style={{ display:'flex', alignItems:'center', gap:12, minWidth:220 }}>
          <div style={{
            width:36, height:36,
            background:'linear-gradient(135deg,#00FF9C,#3D9CFF,#8B5CF6)',
            borderRadius:8, display:'flex', alignItems:'center',
            justifyContent:'center', fontSize:20, flexShrink:0,
          }}>⬡</div>
          <div>
            <div style={{ fontSize:13, fontWeight:700, letterSpacing:'0.15em', color:'#fff' }}>
              AEGIS OMEGA X
            </div>
            <div style={{ fontSize:9, color:'#444', letterSpacing:'0.12em' }}>
              AUGMENTED ENTERPRISE GLOBAL INTELLIGENCE &amp; SECURITY
            </div>
          </div>
        </div>

        {/* Global stats */}
        <div style={{ display:'flex', gap:20, alignItems:'center', flex:1, justifyContent:'center' }}>
          {[
            { l:'GLOBAL RISK',      v:`${(globalRisk*100).toFixed(1)}%`, c:riskColor },
            { l:'ACTIVE LAYERS',    v:'14 / 14',                          c:'#00FF9C' },
            { l:'CRITICAL ALERTS',  v:critAlerts,                         c:'#FF3D3D' },
            { l:'AGENTS RUNNING',   v:agents.filter(a=>a.status==='working').length, c:'#3D9CFF' },
            { l:'KNOWLEDGE NODES',  v:'12.4M',                            c:'#8B5CF6' },
          ].map((s,i)=>(
            <div key={i} style={{ textAlign:'center' }}>
              <div style={{ fontSize:9, color:'#444', letterSpacing:'0.1em' }}>{s.l}</div>
              <div style={{ fontSize:15, fontWeight:700, color:s.c, fontFamily:'monospace' }}>
                {s.v}
              </div>
            </div>
          ))}
        </div>

        <div style={{ fontSize:10, color:'#333', fontFamily:'monospace', minWidth:160, textAlign:'right' }}>
          {currentTime}
        </div>
      </div>

      <div style={{ display:'flex', flex:1, overflow:'hidden' }}>

        {/* ── LAYER SIDEBAR ───────────────────── */}
        <div style={{
          width:200, background:'#080820', borderRight:'1px solid #1a1a4e',
          overflowY:'auto', flexShrink:0,
        }}>
          {layers.map(l => (
            <button key={l.id} onClick={()=>setActiveLayer(l.id)} style={{
              width:'100%', padding:'10px 12px', background:'transparent',
              border:'none', borderBottom:'1px solid #0f0f2a',
              textAlign:'left',
              borderLeft: activeLayer===l.id ? `3px solid ${l.color}` : '3px solid transparent',
              background: activeLayer===l.id ? `${l.color}11` : 'transparent',
            }}>
              <div style={{ display:'flex', alignItems:'center', gap:6, marginBottom:4 }}>
                <span style={{ fontSize:9, color:l.color, fontFamily:'monospace',
                  fontWeight:700, minWidth:24 }}>L{l.id}</span>
                <span style={{ fontSize:10, color: activeLayer===l.id ? '#fff' : '#888',
                  fontWeight: activeLayer===l.id ? 700 : 400, flex:1 }}>
                  {l.shortName}
                </span>
                <span style={{
                  width:6, height:6, borderRadius:'50%', background:l.color,
                  opacity:l.health, flexShrink:0,
                }} />
              </div>
              <MiniBar value={l.health} color={l.color} height={2} />
            </button>
          ))}
        </div>

        {/* ── MAIN CONTENT ───────────────────── */}
        <div style={{ flex:1, overflowY:'auto', padding:16, display:'flex', flexDirection:'column', gap:12 }}>

          {/* Active layer header */}
          <div style={{
            background:'#0a0a1a', border:`1px solid ${active.color}33`,
            borderRadius:8, padding:'12px 16px',
            display:'flex', alignItems:'center', justifyContent:'space-between',
          }}>
            <div>
              <div style={{ fontSize:10, color:active.color, letterSpacing:'0.15em',
                fontWeight:700, marginBottom:4 }}>
                MEGA LAYER {active.id} — {active.shortName}
              </div>
              <div style={{ fontSize:16, fontWeight:700, color:'#fff' }}>{active.name}</div>
            </div>
            <div style={{ display:'flex', gap:16 }}>
              {Object.entries(active.metrics).map(([k,v],i)=>(
                <div key={i} style={{ textAlign:'center' }}>
                  <div style={{ fontSize:9, color:'#555' }}>{k}</div>
                  <div style={{ fontSize:16, fontWeight:700, color:active.color,
                    fontFamily:'monospace' }}>{v}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Layer-specific content */}
          {activeLayer === 5 && (
            /* SOC Alerts */
            <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e', borderRadius:8, padding:16 }}>
              <div style={{ fontSize:11, color:'#888', letterSpacing:'0.1em', fontWeight:700,
                marginBottom:12, display:'flex', alignItems:'center', gap:8 }}>
                <Pulse color='#FF3D3D' /> LIVE SOC ALERT FEED
              </div>
              {alerts.map((a,i)=>(
                <div key={i} style={{
                  display:'grid', gridTemplateColumns:'70px 1fr 70px 60px',
                  gap:8, alignItems:'center', padding:'7px 0',
                  borderBottom:'1px solid #0f0f2a', fontSize:11,
                }}>
                  <span style={{
                    background:`${SEV_COLOR[a.severity]}22`, color:SEV_COLOR[a.severity],
                    padding:'2px 6px', borderRadius:3, fontSize:9,
                    fontWeight:700, letterSpacing:'0.05em', textAlign:'center',
                  }}>{a.severity.toUpperCase()}</span>
                  <span style={{ color:'#ccc' }}>{a.title}</span>
                  <span style={{ color:'#555', fontSize:9 }}>{a.source}</span>
                  <span style={{ color:'#444', fontFamily:'monospace', fontSize:9 }}>T+{a.time}</span>
                </div>
              ))}
              <div style={{ display:'grid', gridTemplateColumns:'repeat(4,1fr)', gap:12, marginTop:16 }}>
                {[
                  { l:'TOTAL ALERTS', v:'1,284', c:'#FF3D3D' },
                  { l:'CRITICAL',     v:'23',    c:'#FF3D3D' },
                  { l:'MTTR',         v:'18min', c:'#00FF9C' },
                  { l:'FP RATE',      v:'4.2%',  c:'#FFB800' },
                ].map((m,i)=>(
                  <div key={i} style={{ background:'#080818', borderRadius:6, padding:'10px 12px',
                    borderTop:`2px solid ${m.c}` }}>
                    <div style={{ fontSize:9, color:'#555', marginBottom:4 }}>{m.l}</div>
                    <div style={{ fontSize:20, fontWeight:700, color:m.c, fontFamily:'monospace' }}>{m.v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeLayer === 6 && (
            /* Predictive Intelligence */
            <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e', borderRadius:8, padding:16 }}>
              <div style={{ fontSize:11, color:'#888', letterSpacing:'0.1em', fontWeight:700, marginBottom:12 }}>
                PREDICTIVE RISK TRAJECTORY — 1 YEAR HORIZON
              </div>
              <svg width="100%" viewBox={`0 0 ${fWidth} ${fHeight+20}`} style={{ overflow:'visible' }}>
                {/* Confidence band */}
                <path d={bandPath} fill="#FFB80015" />
                {/* Grid lines */}
                {[0.25,0.5,0.75,1.0].map((v,i)=>(
                  <line key={i} x1={0} y1={fHeight-v*fHeight}
                    x2={fWidth} y2={fHeight-v*fHeight}
                    stroke="#1a1a3e" strokeWidth={1} strokeDasharray="4 4" />
                ))}
                {/* Forecast line */}
                <path d={fPath} fill="none" stroke="#FFB800" strokeWidth={2}
                  style={{ filter:'drop-shadow(0 0 4px #FFB800)' }} />
                {/* Current risk marker */}
                <circle cx={0} cy={fHeight-globalRisk*fHeight} r={5}
                  fill="#FF3D3D" stroke="#050510" strokeWidth={2} />
                {/* Labels */}
                {['NOW','3M','6M','9M','1YR'].map((l,i)=>(
                  <text key={i} x={(i/4)*fWidth} y={fHeight+16}
                    textAnchor="middle" fontSize={9} fill="#444">{l}</text>
                ))}
              </svg>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12, marginTop:16 }}>
                {[
                  { l:'CURRENT RISK',   v:`${(globalRisk*100).toFixed(1)}%`, c:'#FF3D3D' },
                  { l:'FORECAST (1YR)', v:'52.3%',                           c:'#FFB800' },
                  { l:'MODEL CONF',     v:'89%',                             c:'#00FF9C' },
                ].map((m,i)=>(
                  <div key={i} style={{ background:'#080818', borderRadius:6, padding:'10px 12px',
                    borderTop:`2px solid ${m.c}` }}>
                    <div style={{ fontSize:9, color:'#555', marginBottom:4 }}>{m.l}</div>
                    <div style={{ fontSize:20, fontWeight:700, color:m.c, fontFamily:'monospace' }}>{m.v}</div>
                  </div>
                ))}
              </div>
              <div style={{ marginTop:12, fontSize:11, color:'#666' }}>
                EMERGING THREATS: &nbsp;
                {['AI-assisted phishing','Living-off-the-land v2','Deepfake social eng',
                  'AI agent exploitation'].map((t,i)=>(
                  <span key={i} style={{
                    background:'#FFB80022', color:'#FFB800',
                    padding:'2px 8px', borderRadius:3,
                    fontSize:10, marginRight:6, fontWeight:600,
                  }}>{t}</span>
                ))}
              </div>
            </div>
          )}

          {activeLayer === 4 && (
            /* AI Civilization */
            <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e', borderRadius:8, padding:16 }}>
              <div style={{ fontSize:11, color:'#888', letterSpacing:'0.1em',
                fontWeight:700, marginBottom:12 }}>
                AI AGENT SOCIETY — LIVE STATUS
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(5,1fr)', gap:8 }}>
                {agents.map((a,i)=>(
                  <div key={i} style={{
                    background:'#080818', borderRadius:6, padding:'10px',
                    borderTop:`2px solid ${STATUS_COLOR[a.status]||'#555'}`,
                  }}>
                    <div style={{ fontSize:9, color:STATUS_COLOR[a.status],
                      fontWeight:700, marginBottom:3, letterSpacing:'0.05em' }}>
                      {a.status.toUpperCase()}
                    </div>
                    <div style={{ fontSize:11, color:'#ccc', marginBottom:6 }}>{a.name}</div>
                    <div style={{ fontSize:10, color:'#555', marginBottom:4 }}>Tasks: {a.tasks}</div>
                    <MiniBar value={a.trust} color={a.trust>0.85?'#00FF9C':'#FFB800'} />
                    <div style={{ fontSize:9, color:'#444', marginTop:2 }}>
                      Trust: {(a.trust*100).toFixed(0)}%
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeLayer === 8 && (
            /* Security Economics */
            <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e', borderRadius:8, padding:16 }}>
              <div style={{ fontSize:11, color:'#888', letterSpacing:'0.1em',
                fontWeight:700, marginBottom:12 }}>
                SECURITY ECONOMICS — PORTFOLIO OPTIMIZATION ($2M Budget)
              </div>
              {econ.map((c,i)=>(
                <div key={i} style={{
                  display:'grid', gridTemplateColumns:'180px 60px 1fr 100px',
                  gap:8, alignItems:'center', padding:'7px 0',
                  borderBottom:'1px solid #0f0f2a', fontSize:11,
                  opacity: c.selected ? 1 : 0.4,
                }}>
                  <span style={{ color: c.selected ? '#fff' : '#555', fontWeight: c.selected ? 600 : 400 }}>
                    {c.selected && <span style={{ color:'#00FF9C', marginRight:6 }}>✓</span>}
                    {c.control}
                  </span>
                  <span style={{ color:'#00FF9C', fontFamily:'monospace', fontWeight:700 }}>
                    {c.roi}x ROI
                  </span>
                  <MiniBar value={c.roi} max={5.5} color={c.selected?'#00FF9C':'#333'} />
                  <span style={{ color:'#888', fontFamily:'monospace', textAlign:'right' }}>
                    ${c.cost.toLocaleString()}
                  </span>
                </div>
              ))}
              <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12, marginTop:16 }}>
                {[
                  { l:'PORTFOLIO ROI',  v:'3.2x',  c:'#00FF9C' },
                  { l:'RISK REDUCTION', v:'-42%',   c:'#3D9CFF' },
                  { l:'RESIDUAL RISK',  v:'24.3%',  c:'#FFB800' },
                ].map((m,i)=>(
                  <div key={i} style={{ background:'#080818', borderRadius:6, padding:'10px 12px',
                    borderTop:`2px solid ${m.c}` }}>
                    <div style={{ fontSize:9, color:'#555', marginBottom:4 }}>{m.l}</div>
                    <div style={{ fontSize:20, fontWeight:700, color:m.c, fontFamily:'monospace' }}>{m.v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeLayer === 13 && (
            /* Quantum Safe */
            <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e', borderRadius:8, padding:16 }}>
              <div style={{ fontSize:11, color:'#888', letterSpacing:'0.1em',
                fontWeight:700, marginBottom:12 }}>
                QUANTUM-SAFE CRYPTOGRAPHIC INVENTORY
              </div>
              <table style={{ width:'100%', borderCollapse:'collapse', fontSize:11 }}>
                <thead>
                  <tr style={{ borderBottom:'1px solid #1a1a3e' }}>
                    {['ALGORITHM','QUANTUM SAFE','PQC REPLACEMENT','PRIORITY','FIPS'].map(h=>(
                      <th key={h} style={{ padding:'6px 8px', textAlign:'left',
                        color:'#555', fontWeight:600, fontSize:9, letterSpacing:'0.08em' }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {quantum.map((q,i)=>(
                    <tr key={i} style={{ borderBottom:'1px solid #0f0f2a' }}>
                      <td style={{ padding:'7px 8px', color:'#ccc', fontFamily:'monospace' }}>{q.algorithm}</td>
                      <td style={{ padding:'7px 8px' }}>
                        <span style={{
                          color: q.vulnerable ? '#FF3D3D' : '#00FF9C',
                          fontWeight:700, fontSize:10,
                        }}>
                          {q.vulnerable ? '✗ VULNERABLE' : '✓ SAFE'}
                        </span>
                      </td>
                      <td style={{ padding:'7px 8px', color:'#3D9CFF', fontFamily:'monospace', fontSize:10 }}>
                        {q.pqc}
                      </td>
                      <td style={{ padding:'7px 8px' }}>
                        <span style={{
                          background:`${PRIO_COLOR[q.priority]}22`,
                          color:PRIO_COLOR[q.priority],
                          padding:'2px 8px', borderRadius:3,
                          fontSize:9, fontWeight:700,
                        }}>{q.priority.toUpperCase()}</span>
                      </td>
                      <td style={{ padding:'7px 8px', color:'#555', fontSize:9 }}>
                        {q.vulnerable ? 'FIPS 203/204' : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ marginTop:12, display:'flex', gap:12 }}>
                {[
                  { l:'VULNERABLE', v:'5/8', c:'#FF3D3D' },
                  { l:'SAFE',       v:'3/8', c:'#00FF9C' },
                  { l:'Q-DAY EST',  v:'2030-35', c:'#FFB800' },
                ].map((m,i)=>(
                  <div key={i} style={{ background:'#080818', borderRadius:6,
                    padding:'8px 14px', borderTop:`2px solid ${m.c}` }}>
                    <div style={{ fontSize:9, color:'#555', marginBottom:3 }}>{m.l}</div>
                    <div style={{ fontSize:18, fontWeight:700, color:m.c, fontFamily:'monospace' }}>{m.v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeLayer === 14 && (
            /* Cyber-Physical */
            <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e', borderRadius:8, padding:16 }}>
              <div style={{ fontSize:11, color:'#888', letterSpacing:'0.1em',
                fontWeight:700, marginBottom:12 }}>
                CYBER-PHYSICAL SYSTEM RESILIENCE
              </div>
              {cps.map((s,i)=>(
                <div key={i} style={{ padding:'10px 0', borderBottom:'1px solid #0f0f2a' }}>
                  <div style={{ display:'flex', justifyContent:'space-between',
                    alignItems:'center', marginBottom:6 }}>
                    <div>
                      <span style={{ color:'#fff', fontWeight:600, fontSize:12 }}>{s.name}</span>
                      <span style={{ color:'#555', fontSize:10, marginLeft:8 }}>{s.type}</span>
                    </div>
                    <div style={{ display:'flex', gap:16, fontSize:10 }}>
                      <span style={{ color:'#FF3D3D' }}>Cyber: {(s.cyberRisk*100).toFixed(0)}%</span>
                      <span style={{ color:'#FFB800' }}>Physical: {(s.physRisk*100).toFixed(0)}%</span>
                      <span style={{ color:'#00FF9C' }}>Resilience: {(s.resilience*100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div style={{ display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:8 }}>
                    {[
                      { l:'Cyber Risk', v:s.cyberRisk, c:'#FF3D3D' },
                      { l:'Physical Risk', v:s.physRisk, c:'#FFB800' },
                      { l:'Resilience', v:s.resilience, c:'#00FF9C' },
                    ].map((r,j)=>(
                      <div key={j}>
                        <div style={{ fontSize:9, color:'#555', marginBottom:3 }}>{r.l}</div>
                        <MiniBar value={r.v} color={r.c} />
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Default: show layer overview grid for other layers */}
          {![4,5,6,8,13,14].includes(activeLayer) && (
            <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e',
              borderRadius:8, padding:16, animation:'fadeIn 0.3s ease' }}>
              <div style={{ fontSize:11, color:'#888', letterSpacing:'0.1em',
                fontWeight:700, marginBottom:16 }}>
                LAYER {activeLayer} — ALL METRICS
              </div>
              <div style={{ display:'grid', gridTemplateColumns:'repeat(3,1fr)', gap:12 }}>
                {Object.entries(active.metrics).map(([k,v],i)=>(
                  <div key={i} style={{
                    background:'#080818', borderRadius:6, padding:'12px',
                    borderTop:`2px solid ${active.color}`,
                  }}>
                    <div style={{ fontSize:9, color:'#555', letterSpacing:'0.1em', marginBottom:4 }}>{k}</div>
                    <div style={{ fontSize:24, fontWeight:700,
                      color:active.color, fontFamily:'monospace' }}>{v}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* All-layers health grid */}
          <div style={{ background:'#0a0a1a', border:'1px solid #1a1a3e',
            borderRadius:8, padding:16 }}>
            <div style={{ fontSize:11, color:'#888', letterSpacing:'0.1em',
              fontWeight:700, marginBottom:12 }}>
              ALL LAYERS — SYSTEM HEALTH
            </div>
            <div style={{ display:'grid', gridTemplateColumns:'repeat(7,1fr)', gap:6 }}>
              {layers.map(l=>(
                <button key={l.id}
                  onClick={()=>setActiveLayer(l.id)}
                  style={{
                    background: activeLayer===l.id ? `${l.color}22` : '#080818',
                    border:`1px solid ${l.color}${activeLayer===l.id?'88':'33'}`,
                    borderRadius:6, padding:'8px 6px', textAlign:'center',
                  }}>
                  <div style={{ fontSize:9, color:l.color, fontWeight:700,
                    letterSpacing:'0.05em', marginBottom:3 }}>L{l.id}</div>
                  <div style={{ fontSize:9, color:'#888', marginBottom:5 }}>
                    {l.shortName}
                  </div>
                  <MiniBar value={l.health} color={l.color} />
                  <div style={{ fontSize:9, color:l.color, marginTop:3, fontFamily:'monospace' }}>
                    {(l.health*100).toFixed(0)}%
                  </div>
                </button>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
