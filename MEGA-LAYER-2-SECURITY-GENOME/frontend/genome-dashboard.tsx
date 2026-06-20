// AEGIS OMEGA X — MEGA LAYER 2
// ENTERPRISE SECURITY GENOME — NEXT.JS DASHBOARD
// frontend/genome-dashboard.tsx

'use client';

import { useEffect, useState, useRef } from 'react';

// ──────────────────────────────────────────────
// TYPES
// ──────────────────────────────────────────────

interface MutationEvent {
  mutation_id:   string;
  mutation_type: string;
  node_id:       string;
  node_type:     string;
  severity:      string;
  risk_delta:    number;
  source:        string;
  occurred_at:   string;
}

interface ResilienceDimension {
  label:  string;
  score:  number;
  target: number;
  color:  string;
}

interface GenomeStat {
  label: string;
  value: string | number;
  color: string;
  sub?:  string;
}

// ──────────────────────────────────────────────
// MOCK DATA GENERATORS
// ──────────────────────────────────────────────

const MUTATION_TYPES = [
  'asset_modified', 'cve_introduced', 'privilege_escalated',
  'mfa_disabled', 'port_opened', 'config_changed',
  'secret_exposed', 'control_removed', 'dependency_added',
  'firewall_rule_removed', 'trust_added', 'cve_patched',
];
const SEVERITIES = ['critical','high','medium','low'];
const SOURCES = ['aws_inspector','nuclei','trivy','iam_scanner','iac_scanner','osquery'];
const NODE_TYPES = ['asset','identity','dependency','configuration','security_control'];
const SEV_COLOR: Record<string,string> = {
  critical: '#FF3D3D', high: '#FF8C00', medium: '#FFB800', low: '#00FF9C'
};

function makeMutation(i: number): MutationEvent {
  const sev = SEVERITIES[Math.floor(Math.random() * SEVERITIES.length)];
  return {
    mutation_id:   `mut-${i.toString().padStart(6,'0')}`,
    mutation_type: MUTATION_TYPES[Math.floor(Math.random() * MUTATION_TYPES.length)],
    node_id:       `node-${Math.floor(Math.random()*9999).toString().padStart(4,'0')}`,
    node_type:     NODE_TYPES[Math.floor(Math.random() * NODE_TYPES.length)],
    severity:      sev,
    risk_delta:    parseFloat((Math.random() * 0.4 - 0.05).toFixed(3)),
    source:        SOURCES[Math.floor(Math.random() * SOURCES.length)],
    occurred_at:   new Date(Date.now() - Math.random() * 3600000).toISOString(),
  };
}

const RESILIENCE_DIMS: ResilienceDimension[] = [
  { label: 'Control Coverage',    score: 0.76, target: 0.95, color: '#3D9CFF' },
  { label: 'Patch Velocity',      score: 0.61, target: 0.90, color: '#00FF9C' },
  { label: 'Identity Hygiene',    score: 0.54, target: 0.85, color: '#FFB800' },
  { label: 'Encryption Coverage', score: 0.83, target: 1.00, color: '#8B5CF6' },
  { label: 'Network Segmentation',score: 0.47, target: 0.80, color: '#FF8C00' },
  { label: 'Redundancy',          score: 0.69, target: 0.90, color: '#00D4FF' },
  { label: 'Recovery Speed',      score: 0.72, target: 0.85, color: '#00FF9C' },
  { label: 'Blast Radius Score',  score: 0.58, target: 0.80, color: '#FFB800' },
];

// ──────────────────────────────────────────────
// SUB-COMPONENTS
// ──────────────────────────────────────────────

function ResilienceRadar({ dims }: { dims: ResilienceDimension[] }) {
  const size = 220;
  const cx = size / 2;
  const cy = size / 2;
  const r  = 80;
  const n  = dims.length;

  const points = (values: number[]) =>
    values.map((v, i) => {
      const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
      return {
        x: cx + r * v * Math.cos(angle),
        y: cy + r * v * Math.sin(angle),
      };
    });

  const toPath = (pts: {x:number;y:number}[]) =>
    pts.map((p,i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ') + ' Z';

  const scores  = dims.map(d => d.score);
  const targets = dims.map(d => d.target);
  const scorePts  = points(scores);
  const targetPts = points(targets);

  // Axis endpoints
  const axisEnds = dims.map((_, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  });

  // Label positions (further out)
  const labelPts = dims.map((d, i) => {
    const angle = (Math.PI * 2 * i) / n - Math.PI / 2;
    return {
      x: cx + (r + 28) * Math.cos(angle),
      y: cy + (r + 28) * Math.sin(angle),
      label: d.label.split(' ')[0],
    };
  });

  return (
    <svg width={size} height={size} style={{ overflow: 'visible' }}>
      {/* Grid rings */}
      {[0.25, 0.5, 0.75, 1.0].map((ring, ri) => {
        const ringPts = points(Array(n).fill(ring));
        return (
          <polygon
            key={ri}
            points={ringPts.map(p => `${p.x},${p.y}`).join(' ')}
            fill="none"
            stroke="#1a1a3e"
            strokeWidth={1}
          />
        );
      })}
      {/* Axes */}
      {axisEnds.map((end, i) => (
        <line key={i} x1={cx} y1={cy} x2={end.x} y2={end.y}
              stroke="#1a1a3e" strokeWidth={1} />
      ))}
      {/* Target area */}
      <polygon
        points={targetPts.map(p => `${p.x},${p.y}`).join(' ')}
        fill="#3D9CFF08"
        stroke="#3D9CFF"
        strokeWidth={1}
        strokeDasharray="4 2"
      />
      {/* Score area */}
      <polygon
        points={scorePts.map(p => `${p.x},${p.y}`).join(' ')}
        fill="#00FF9C20"
        stroke="#00FF9C"
        strokeWidth={2}
      />
      {/* Score dots */}
      {scorePts.map((p, i) => (
        <circle key={i} cx={p.x} cy={p.y} r={4}
                fill={dims[i].color} stroke="#050510" strokeWidth={2} />
      ))}
      {/* Labels */}
      {labelPts.map((lp, i) => (
        <text key={i} x={lp.x} y={lp.y}
              textAnchor="middle" dominantBaseline="middle"
              fontSize="9" fill="#666">
          {lp.label}
        </text>
      ))}
    </svg>
  );
}


function MutationFeed({ mutations }: { mutations: MutationEvent[] }) {
  return (
    <div style={{ overflowY: 'auto', maxHeight: '420px' }}>
      {mutations.map((m, i) => (
        <div key={i} style={{
          display: 'grid',
          gridTemplateColumns: '90px 1fr 90px 70px 70px',
          gap: '8px',
          alignItems: 'center',
          padding: '8px 0',
          borderBottom: '1px solid #0f0f2a',
          fontSize: '11px',
        }}>
          <span style={{
            background: `${SEV_COLOR[m.severity]}22`,
            color: SEV_COLOR[m.severity],
            padding: '2px 6px',
            borderRadius: '4px',
            fontSize: '10px',
            fontWeight: 700,
            textAlign: 'center',
            letterSpacing: '0.05em',
          }}>
            {m.severity.toUpperCase()}
          </span>

          <div>
            <div style={{ color: '#ddd', fontFamily: 'monospace', marginBottom: '2px' }}>
              {m.mutation_type}
            </div>
            <div style={{ color: '#555', fontSize: '10px' }}>
              {m.node_type} · {m.node_id} · {m.source}
            </div>
          </div>

          <span style={{
            color: m.risk_delta > 0 ? '#FF3D3D' : '#00FF9C',
            fontFamily: 'monospace', fontWeight: 700,
          }}>
            {m.risk_delta > 0 ? '↑' : '↓'} {Math.abs(m.risk_delta).toFixed(3)}
          </span>

          <span style={{ color: '#555', fontSize: '10px' }}>
            {new Date(m.occurred_at).toLocaleTimeString()}
          </span>

          <span style={{
            color: '#444', fontSize: '10px', fontFamily: 'monospace',
          }}>
            {m.mutation_id.slice(-6)}
          </span>
        </div>
      ))}
    </div>
  );
}


function DNAFingerprint({ hash }: { hash: string }) {
  return (
    <div style={{
      fontFamily: 'monospace',
      fontSize: '11px',
      color: '#00FF9C',
      wordBreak: 'break-all',
      lineHeight: '1.8',
      letterSpacing: '0.05em',
    }}>
      {hash.match(/.{1,8}/g)?.map((chunk, i) => (
        <span key={i} style={{
          marginRight: '4px',
          opacity: 0.5 + (i / 8) * 0.5,
        }}>
          {chunk}
        </span>
      ))}
    </div>
  );
}


// ──────────────────────────────────────────────
// MAIN DASHBOARD
// ──────────────────────────────────────────────

export default function GenomeDashboard() {
  const [mutations, setMutations] = useState<MutationEvent[]>(
    () => Array.from({ length: 40 }, (_, i) => makeMutation(i))
  );
  const [mutCount, setMutCount] = useState(40);
  const [resilience, setResilience] = useState(RESILIENCE_DIMS);
  const [genomeHash, setGenomeHash] = useState('a3f8d1b2c4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3');
  const [overallRisk, setOverallRisk] = useState(0.412);
  const [ticker, setTicker] = useState(0);

  // Live mutation stream
  useEffect(() => {
    const interval = setInterval(() => {
      const newMut = makeMutation(mutCount);
      setMutations(prev => [newMut, ...prev.slice(0, 49)]);
      setMutCount(c => c + 1);
      setTicker(t => t + 1);

      // Drift overall risk
      setOverallRisk(prev =>
        Math.max(0.05, Math.min(0.95, prev + (Math.random() - 0.48) * 0.01))
      );

      // Occasionally update resilience dims
      if (Math.random() < 0.2) {
        setResilience(prev => prev.map(d => ({
          ...d,
          score: Math.max(0.1, Math.min(0.99, d.score + (Math.random() - 0.48) * 0.02))
        })));
      }

      // New genome hash every 10 mutations
      if (mutCount % 10 === 0) {
        setGenomeHash(
          Array.from({ length: 48 }, () =>
            Math.floor(Math.random() * 16).toString(16)
          ).join('')
        );
      }
    }, 1500);
    return () => clearInterval(interval);
  }, [mutCount]);

  const criticalCount = mutations.filter(m => m.severity === 'critical').length;
  const highCount     = mutations.filter(m => m.severity === 'high').length;
  const overallRes    = resilience.reduce((s,d) => s + d.score, 0) / resilience.length;
  const riskColor     = overallRisk > 0.7 ? '#FF3D3D' : overallRisk > 0.4 ? '#FFB800' : '#00FF9C';

  return (
    <div style={{
      minHeight: '100vh',
      background: '#050510',
      color: '#e0e0ff',
      fontFamily: 'system-ui, -apple-system, monospace',
    }}>
      <style>{`
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.3} }
        @keyframes glow  { 0%,100%{box-shadow:0 0 8px #00FF9C44} 50%{box-shadow:0 0 20px #00FF9C88} }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-thumb { background: #1a1a4e; }
      `}</style>

      {/* HEADER */}
      <div style={{
        background: '#080820',
        borderBottom: '1px solid #1a1a4e',
        padding: '12px 24px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '32px', height: '32px',
            background: 'linear-gradient(135deg, #FF3D3D, #FF8C00)',
            borderRadius: '50%', display: 'flex',
            alignItems: 'center', justifyContent: 'center', fontSize: '16px',
          }}>🧬</div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, letterSpacing: '0.15em', color: '#fff' }}>
              AEGIS OMEGA X
            </div>
            <div style={{ fontSize: '10px', color: '#555', letterSpacing: '0.1em' }}>
              MEGA LAYER 2 · ENTERPRISE SECURITY GENOME
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '32px' }}>
          {[
            { label: 'GENOME RISK',  value: `${(overallRisk*100).toFixed(1)}%`, color: riskColor },
            { label: 'RESILIENCE',   value: `${(overallRes*100).toFixed(1)}%`,  color: '#00FF9C' },
            { label: 'MUTATIONS/HR', value: `${mutCount}`,                      color: '#FFB800' },
            { label: 'CRITICAL',     value: criticalCount,                       color: '#FF3D3D' },
          ].map((stat, i) => (
            <div key={i} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '10px', color: '#555' }}>{stat.label}</div>
              <div style={{
                fontSize: '18px', fontWeight: 700,
                color: stat.color, fontFamily: 'monospace',
              }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: '20px 24px', maxWidth: '1600px', margin: '0 auto' }}>

        {/* GENOME STATS ROW */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(6, 1fr)',
          gap: '12px', marginBottom: '20px',
        }}>
          {[
            { label: 'TOTAL NODES',     value: '4,891',  color: '#3D9CFF',  sub: 'genome nodes' },
            { label: 'GENOME EDGES',    value: '23,441', color: '#8B5CF6',  sub: 'relationships' },
            { label: 'ACTIVE CVEs',     value: '187',    color: '#FF3D3D',  sub: '23 critical' },
            { label: 'ORPHANED ASSETS', value: '34',     color: '#FF8C00',  sub: 'no controls' },
            { label: 'OVERPRIV IDS',    value: '29',     color: '#FFB800',  sub: 'need review' },
            { label: 'GENOME VERSION',  value: 'v7.291', color: '#00FF9C',  sub: 'latest snapshot' },
          ].map((s, i) => (
            <div key={i} style={{
              background: '#0a0a1a',
              border: `1px solid ${s.color}22`,
              borderRadius: '8px',
              padding: '14px 16px',
              position: 'relative', overflow: 'hidden',
            }}>
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0,
                height: '2px', background: s.color, boxShadow: `0 0 8px ${s.color}`,
              }} />
              <div style={{ fontSize: '10px', color: '#666', letterSpacing: '0.1em', marginBottom: '6px' }}>
                {s.label}
              </div>
              <div style={{ fontSize: '22px', fontWeight: 700, color: s.color, fontFamily: 'monospace' }}>
                {s.value}
              </div>
              <div style={{ fontSize: '10px', color: '#444', marginTop: '3px' }}>{s.sub}</div>
            </div>
          ))}
        </div>

        {/* MAIN GRID */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: '20px', marginBottom: '20px' }}>

          {/* MUTATION FEED */}
          <div style={{
            background: '#0a0a1a',
            border: '1px solid #1a1a3e',
            borderRadius: '8px', padding: '20px',
          }}>
            <div style={{
              display: 'flex', justifyContent: 'space-between',
              alignItems: 'center', marginBottom: '16px',
            }}>
              <div style={{
                fontSize: '11px', color: '#888',
                letterSpacing: '0.1em', fontWeight: 700,
                display: 'flex', alignItems: 'center', gap: '8px',
              }}>
                <span style={{
                  width: '8px', height: '8px', borderRadius: '50%',
                  background: '#00FF9C', display: 'inline-block',
                  animation: 'pulse 1s infinite',
                }} />
                LIVE MUTATION FEED
              </div>
              <div style={{ display: 'flex', gap: '8px' }}>
                {(['critical','high','medium','low'] as const).map(sev => (
                  <span key={sev} style={{
                    background: `${SEV_COLOR[sev]}22`,
                    color: SEV_COLOR[sev],
                    padding: '2px 8px',
                    borderRadius: '4px',
                    fontSize: '10px',
                    fontWeight: 700,
                  }}>
                    {mutations.filter(m => m.severity === sev).length} {sev}
                  </span>
                ))}
              </div>
            </div>
            <MutationFeed mutations={mutations} />
          </div>

          {/* RESILIENCE RADAR + DNA */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {/* Radar */}
            <div style={{
              background: '#0a0a1a',
              border: '1px solid #1a1a3e',
              borderRadius: '8px', padding: '20px',
              display: 'flex', flexDirection: 'column', alignItems: 'center',
            }}>
              <div style={{
                fontSize: '11px', color: '#888', letterSpacing: '0.1em',
                fontWeight: 700, marginBottom: '12px', alignSelf: 'flex-start',
              }}>
                RESILIENCE GENOME
              </div>
              <ResilienceRadar dims={resilience} />
              <div style={{
                marginTop: '12px', fontSize: '24px', fontWeight: 700,
                color: '#00FF9C', fontFamily: 'monospace',
              }}>
                {(overallRes * 100).toFixed(1)}%
              </div>
              <div style={{ fontSize: '10px', color: '#555', marginTop: '4px' }}>
                OVERALL RESILIENCE SCORE
              </div>
            </div>

            {/* DNA Fingerprint */}
            <div style={{
              background: '#0a0a1a',
              border: '1px solid #00FF9C22',
              borderRadius: '8px', padding: '16px',
            }}>
              <div style={{
                fontSize: '11px', color: '#888', letterSpacing: '0.1em',
                fontWeight: 700, marginBottom: '10px',
              }}>
                GENOME DNA HASH
              </div>
              <DNAFingerprint hash={genomeHash} />
              <div style={{
                marginTop: '8px', fontSize: '10px', color: '#444',
                fontFamily: 'monospace',
              }}>
                v7.{mutCount.toString().padStart(3,'0')} · {new Date().toISOString().slice(11,19)} UTC
              </div>
            </div>
          </div>
        </div>

        {/* RESILIENCE DIMENSIONS */}
        <div style={{
          background: '#0a0a1a',
          border: '1px solid #1a1a3e',
          borderRadius: '8px', padding: '20px',
        }}>
          <div style={{
            fontSize: '11px', color: '#888', letterSpacing: '0.1em',
            fontWeight: 700, marginBottom: '16px',
          }}>
            RESILIENCE DIMENSIONS — CURRENT vs TARGET
          </div>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(4, 1fr)',
            gap: '20px',
          }}>
            {resilience.map((dim, i) => (
              <div key={i}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontSize: '11px', marginBottom: '6px',
                }}>
                  <span style={{ color: '#aaa' }}>{dim.label}</span>
                  <span style={{ color: dim.color, fontFamily: 'monospace', fontWeight: 700 }}>
                    {(dim.score * 100).toFixed(0)}%
                    <span style={{ color: '#444', fontWeight: 400 }}>
                      /{(dim.target * 100).toFixed(0)}%
                    </span>
                  </span>
                </div>
                {/* Target bar */}
                <div style={{ height: '8px', background: '#1a1a3e', borderRadius: '4px', position: 'relative' }}>
                  {/* Target marker */}
                  <div style={{
                    position: 'absolute',
                    left: `${dim.target * 100}%`,
                    top: 0, bottom: 0,
                    width: '2px',
                    background: '#333',
                    transform: 'translateX(-1px)',
                  }} />
                  {/* Score bar */}
                  <div style={{
                    height: '100%',
                    width: `${dim.score * 100}%`,
                    background: dim.color,
                    borderRadius: '4px',
                    boxShadow: `0 0 8px ${dim.color}66`,
                    transition: 'width 0.5s ease',
                  }} />
                </div>
                <div style={{ fontSize: '10px', color: '#333', marginTop: '3px' }}>
                  gap: {((dim.target - dim.score) * 100).toFixed(1)}%
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
