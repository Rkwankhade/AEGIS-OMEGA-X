// AEGIS OMEGA X — MEGA LAYER 1
// PLANETARY DIGITAL TWIN — NEXT.JS DASHBOARD
// frontend/app/page.tsx

'use client';

import { useEffect, useState, useCallback } from 'react';
import dynamic from 'next/dynamic';

const ForceGraph = dynamic(() => import('../components/PlanetaryGraph'), { ssr: false });
const CascadeSimulator = dynamic(() => import('../components/CascadeSimulator'), { ssr: false });

// ──────────────────────────────────────────────
// TYPES
// ──────────────────────────────────────────────

interface PlanetaryHealth {
  total_entities: number;
  total_assets: number;
  total_relationships: number;
  global_risk_score: number;
  critical_entities: number;
  compromised_assets: number;
  active_cascades: number;
  snapshot_at: string;
}

interface SimTick {
  tick_number: number;
  global_risk_score: number;
  compromised_assets: number;
  active_cascades: number;
}

// ──────────────────────────────────────────────
// MOCK DATA (replace with real API calls)
// ──────────────────────────────────────────────

const MOCK_HEALTH: PlanetaryHealth = {
  total_entities: 10247,
  total_assets: 1_284_903,
  total_relationships: 48_291_034,
  global_risk_score: 0.347,
  critical_entities: 89,
  compromised_assets: 234,
  active_cascades: 3,
  snapshot_at: new Date().toISOString(),
};

const DOMAINS = [
  { name: 'Enterprise',    count: 4200, risk: 0.31, color: '#00FF9C' },
  { name: 'Financial',     count: 1800, risk: 0.68, color: '#FF3D3D' },
  { name: 'Healthcare',    count: 980,  risk: 0.52, color: '#FFB800' },
  { name: 'Government',    count: 720,  risk: 0.44, color: '#3D9CFF' },
  { name: 'Energy',        count: 340,  risk: 0.71, color: '#FF3D3D' },
  { name: 'Telecom',       count: 590,  risk: 0.39, color: '#00FF9C' },
  { name: 'Transport',     count: 410,  risk: 0.48, color: '#FFB800' },
  { name: 'Cloud',         count: 280,  risk: 0.29, color: '#00FF9C' },
  { name: 'Manufacturing', count: 620,  risk: 0.55, color: '#FFB800' },
  { name: 'AI Ecosystem',  count: 307,  risk: 0.62, color: '#FF8C00' },
];

// ──────────────────────────────────────────────
// COMPONENTS
// ──────────────────────────────────────────────

function RiskBar({ score }: { score: number }) {
  const pct = (score * 100).toFixed(1);
  const color = score > 0.7 ? '#FF3D3D' : score > 0.4 ? '#FFB800' : '#00FF9C';
  return (
    <div style={{ width: '100%' }}>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: '11px', color: '#888', marginBottom: '4px'
      }}>
        <span>RISK</span>
        <span style={{ color, fontWeight: 700 }}>{pct}%</span>
      </div>
      <div style={{ height: '4px', background: '#1a1a2e', borderRadius: '2px' }}>
        <div style={{
          height: '100%', width: `${pct}%`,
          background: color, borderRadius: '2px',
          boxShadow: `0 0 8px ${color}`,
          transition: 'width 1s ease',
        }} />
      </div>
    </div>
  );
}

function MetricCard({
  label, value, sub, color = '#00FF9C', pulse = false
}: {
  label: string; value: string | number; sub?: string;
  color?: string; pulse?: boolean;
}) {
  return (
    <div style={{
      background: '#0a0a1a',
      border: `1px solid ${color}22`,
      borderRadius: '8px',
      padding: '16px 20px',
      position: 'relative',
      overflow: 'hidden',
    }}>
      <div style={{
        position: 'absolute', top: 0, left: 0, right: 0,
        height: '2px', background: color,
        boxShadow: `0 0 12px ${color}`,
      }} />
      <div style={{ fontSize: '11px', color: '#888', letterSpacing: '0.1em', marginBottom: '8px' }}>
        {label}
      </div>
      <div style={{
        fontSize: '28px', fontWeight: 700,
        color, fontFamily: 'monospace',
        display: 'flex', alignItems: 'center', gap: '8px',
      }}>
        {value}
        {pulse && (
          <span style={{
            display: 'inline-block', width: '8px', height: '8px',
            borderRadius: '50%', background: color,
            animation: 'pulse 1.5s infinite',
          }} />
        )}
      </div>
      {sub && <div style={{ fontSize: '11px', color: '#555', marginTop: '4px' }}>{sub}</div>}
    </div>
  );
}

function DomainTable() {
  return (
    <div style={{
      background: '#0a0a1a',
      border: '1px solid #1a1a3e',
      borderRadius: '8px',
      padding: '20px',
    }}>
      <div style={{
        fontSize: '11px', color: '#888', letterSpacing: '0.1em',
        marginBottom: '16px', fontWeight: 700
      }}>
        DOMAIN TWIN STATUS
      </div>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
        <thead>
          <tr style={{ borderBottom: '1px solid #1a1a3e' }}>
            {['DOMAIN', 'ENTITIES', 'AVG RISK', 'STATUS'].map(h => (
              <th key={h} style={{
                textAlign: 'left', padding: '6px 8px',
                color: '#555', fontWeight: 600, letterSpacing: '0.08em',
              }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {DOMAINS.map((d, i) => (
            <tr key={i} style={{ borderBottom: '1px solid #0f0f2a' }}>
              <td style={{ padding: '8px', color: '#ccc', fontFamily: 'monospace' }}>{d.name}</td>
              <td style={{ padding: '8px', color: '#888', fontFamily: 'monospace' }}>
                {d.count.toLocaleString()}
              </td>
              <td style={{ padding: '8px' }}>
                <span style={{
                  color: d.color, fontFamily: 'monospace', fontWeight: 700,
                }}>
                  {(d.risk * 100).toFixed(0)}%
                </span>
              </td>
              <td style={{ padding: '8px' }}>
                <span style={{
                  background: d.risk > 0.6 ? '#FF3D3D22' : d.risk > 0.4 ? '#FFB80022' : '#00FF9C22',
                  color: d.color,
                  padding: '2px 8px',
                  borderRadius: '4px',
                  fontSize: '10px',
                  fontWeight: 700,
                  letterSpacing: '0.1em',
                }}>
                  {d.risk > 0.6 ? 'ELEVATED' : d.risk > 0.4 ? 'MODERATE' : 'NOMINAL'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function TickTimeline({ ticks }: { ticks: SimTick[] }) {
  const max = Math.max(...ticks.map(t => t.global_risk_score), 0.01);
  return (
    <div style={{
      background: '#0a0a1a',
      border: '1px solid #1a1a3e',
      borderRadius: '8px',
      padding: '20px',
    }}>
      <div style={{
        fontSize: '11px', color: '#888', letterSpacing: '0.1em',
        marginBottom: '16px', fontWeight: 700
      }}>
        SIMULATION TICK HISTORY — GLOBAL RISK
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: '3px', height: '80px' }}>
        {ticks.map((t, i) => (
          <div
            key={i}
            title={`Tick ${t.tick_number}: ${(t.global_risk_score * 100).toFixed(1)}%`}
            style={{
              flex: 1,
              height: `${(t.global_risk_score / max) * 100}%`,
              background: t.global_risk_score > 0.7 ? '#FF3D3D'
                : t.global_risk_score > 0.4 ? '#FFB800'
                : '#00FF9C',
              borderRadius: '2px 2px 0 0',
              opacity: 0.7 + (i / ticks.length) * 0.3,
              transition: 'height 0.3s ease',
            }}
          />
        ))}
      </div>
      <div style={{
        display: 'flex', justifyContent: 'space-between',
        fontSize: '10px', color: '#444', marginTop: '6px',
      }}>
        <span>TICK {ticks[0]?.tick_number ?? 0}</span>
        <span>NOW</span>
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────
// MAIN PAGE
// ──────────────────────────────────────────────

export default function PDTDashboard() {
  const [health, setHealth] = useState<PlanetaryHealth>(MOCK_HEALTH);
  const [ticks, setTicks] = useState<SimTick[]>(() =>
    Array.from({ length: 60 }, (_, i) => ({
      tick_number: i,
      global_risk_score: 0.2 + Math.random() * 0.3,
      compromised_assets: Math.floor(Math.random() * 50),
      active_cascades: Math.floor(Math.random() * 5),
    }))
  );
  const [currentTime, setCurrentTime] = useState('');
  const [selectedDomain, setSelectedDomain] = useState<string | null>(null);

  // Simulate live ticks
  useEffect(() => {
    const interval = setInterval(() => {
      const newTick: SimTick = {
        tick_number: ticks[ticks.length - 1].tick_number + 1,
        global_risk_score: Math.max(0.05, Math.min(0.95,
          ticks[ticks.length - 1].global_risk_score + (Math.random() - 0.48) * 0.05
        )),
        compromised_assets: Math.floor(Math.random() * 300),
        active_cascades: Math.floor(Math.random() * 8),
      };
      setTicks(prev => [...prev.slice(-59), newTick]);
      setHealth(prev => ({
        ...prev,
        global_risk_score: newTick.global_risk_score,
        compromised_assets: newTick.compromised_assets,
        active_cascades: newTick.active_cascades,
        snapshot_at: new Date().toISOString(),
      }));
    }, 1000);
    return () => clearInterval(interval);
  }, [ticks]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(new Date().toISOString().replace('T', ' ').slice(0, 19) + ' UTC');
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const riskColor = health.global_risk_score > 0.7 ? '#FF3D3D'
    : health.global_risk_score > 0.4 ? '#FFB800'
    : '#00FF9C';

  return (
    <div style={{
      minHeight: '100vh',
      background: '#050510',
      color: '#e0e0ff',
      fontFamily: 'system-ui, -apple-system, monospace',
      padding: '0',
    }}>
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.4; transform: scale(0.8); }
        }
        @keyframes scan {
          0% { transform: translateY(-100%); }
          100% { transform: translateY(100vh); }
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: #050510; }
        ::-webkit-scrollbar-thumb { background: #1a1a4e; }
      `}</style>

      {/* HEADER */}
      <div style={{
        background: '#080820',
        borderBottom: '1px solid #1a1a4e',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{
            width: '32px', height: '32px',
            background: 'linear-gradient(135deg, #00FF9C, #0080FF)',
            borderRadius: '6px',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '16px',
          }}>⬡</div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: 700, letterSpacing: '0.15em', color: '#fff' }}>
              AEGIS OMEGA X
            </div>
            <div style={{ fontSize: '10px', color: '#555', letterSpacing: '0.1em' }}>
              MEGA LAYER 1 · PLANETARY DIGITAL TWIN
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#555' }}>GLOBAL RISK</div>
            <div style={{ fontSize: '18px', fontWeight: 700, color: riskColor, fontFamily: 'monospace' }}>
              {(health.global_risk_score * 100).toFixed(1)}%
            </div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: '10px', color: '#555' }}>ACTIVE CASCADES</div>
            <div style={{
              fontSize: '18px', fontWeight: 700,
              color: health.active_cascades > 0 ? '#FF3D3D' : '#00FF9C',
              fontFamily: 'monospace',
            }}>
              {health.active_cascades}
            </div>
          </div>
          <div style={{ fontSize: '11px', color: '#444', fontFamily: 'monospace' }}>
            {currentTime}
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div style={{ padding: '20px 24px', maxWidth: '1600px', margin: '0 auto' }}>

        {/* METRIC CARDS */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '12px',
          marginBottom: '20px',
        }}>
          <MetricCard
            label="ENTITIES MODELED"
            value={health.total_entities.toLocaleString()}
            sub="across 13 domain twins"
            color="#3D9CFF"
          />
          <MetricCard
            label="DIGITAL ASSETS"
            value={(health.total_assets / 1_000_000).toFixed(2) + 'M'}
            sub="continuously tracked"
            color="#00FF9C"
          />
          <MetricCard
            label="GRAPH RELATIONSHIPS"
            value={(health.total_relationships / 1_000_000).toFixed(1) + 'M'}
            sub="edges in planetary graph"
            color="#8B5CF6"
          />
          <MetricCard
            label="COMPROMISED ASSETS"
            value={health.compromised_assets.toLocaleString()}
            sub="active incidents"
            color={health.compromised_assets > 100 ? '#FF3D3D' : '#FFB800'}
            pulse={health.compromised_assets > 0}
          />
          <MetricCard
            label="CRITICAL ENTITIES"
            value={health.critical_entities}
            sub="criticality > 0.9"
            color="#FF8C00"
          />
          <MetricCard
            label="ACTIVE CASCADES"
            value={health.active_cascades}
            sub="propagating now"
            color={health.active_cascades > 0 ? '#FF3D3D' : '#00FF9C'}
            pulse={health.active_cascades > 0}
          />
        </div>

        {/* TICK TIMELINE */}
        <div style={{ marginBottom: '20px' }}>
          <TickTimeline ticks={ticks} />
        </div>

        {/* DOMAIN TABLE + GLOBAL RISK */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 320px',
          gap: '20px',
          marginBottom: '20px',
        }}>
          <DomainTable />

          <div style={{
            background: '#0a0a1a',
            border: '1px solid #1a1a3e',
            borderRadius: '8px',
            padding: '20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
          }}>
            <div style={{
              fontSize: '11px', color: '#888', letterSpacing: '0.1em', fontWeight: 700
            }}>
              PLANETARY RISK BREAKDOWN
            </div>

            {[
              { label: 'Financial Sector', score: 0.68, color: '#FF3D3D' },
              { label: 'Energy Grid',      score: 0.71, color: '#FF3D3D' },
              { label: 'Healthcare',       score: 0.52, color: '#FFB800' },
              { label: 'Manufacturing',    score: 0.55, color: '#FFB800' },
              { label: 'AI Ecosystem',     score: 0.62, color: '#FF8C00' },
              { label: 'Government',       score: 0.44, color: '#FFB800' },
              { label: 'Enterprise',       score: 0.31, color: '#00FF9C' },
              { label: 'Cloud Providers',  score: 0.29, color: '#00FF9C' },
            ].map((item, i) => (
              <div key={i}>
                <div style={{
                  display: 'flex', justifyContent: 'space-between',
                  fontSize: '12px', color: '#ccc', marginBottom: '6px',
                }}>
                  <span>{item.label}</span>
                  <span style={{ color: item.color, fontFamily: 'monospace', fontWeight: 700 }}>
                    {(item.score * 100).toFixed(0)}%
                  </span>
                </div>
                <div style={{ height: '3px', background: '#1a1a3e', borderRadius: '2px' }}>
                  <div style={{
                    height: '100%',
                    width: `${item.score * 100}%`,
                    background: item.color,
                    borderRadius: '2px',
                    boxShadow: `0 0 6px ${item.color}`,
                  }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CASCADE EVENTS */}
        <div style={{
          background: '#0a0a1a',
          border: '1px solid #FF3D3D22',
          borderRadius: '8px',
          padding: '20px',
        }}>
          <div style={{
            fontSize: '11px', color: '#888', letterSpacing: '0.1em',
            fontWeight: 700, marginBottom: '16px',
            display: 'flex', alignItems: 'center', gap: '8px',
          }}>
            <span style={{
              width: '8px', height: '8px', borderRadius: '50%',
              background: '#FF3D3D', display: 'inline-block',
              animation: 'pulse 1s infinite',
            }} />
            ACTIVE CASCADE EVENTS
          </div>

          {[
            {
              id: 'CSC-2024-0891',
              origin: 'core-banking-api-prod',
              entity: 'GlobalBank Corp',
              blast: 47,
              severity: 'CRITICAL',
              impact: '$2.3M',
              tick: 'T+00:03:21',
            },
            {
              id: 'CSC-2024-0892',
              origin: 'power-scada-node-12',
              entity: 'NationalGrid East',
              blast: 12,
              severity: 'HIGH',
              impact: '$890K',
              tick: 'T+00:01:44',
            },
            {
              id: 'CSC-2024-0893',
              origin: 'ehr-api-gateway',
              entity: 'Metro Health System',
              blast: 8,
              severity: 'HIGH',
              impact: '$420K',
              tick: 'T+00:00:32',
            },
          ].map((evt, i) => (
            <div key={i} style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 80px 100px 80px 120px',
              gap: '8px',
              alignItems: 'center',
              padding: '10px 0',
              borderBottom: '1px solid #0f0f2a',
              fontSize: '12px',
            }}>
              <span style={{ color: '#FF3D3D', fontFamily: 'monospace', fontWeight: 700 }}>
                {evt.id}
              </span>
              <span style={{ color: '#ccc', fontFamily: 'monospace' }}>{evt.origin}</span>
              <span style={{ color: '#888' }}>{evt.entity.slice(0, 12)}..</span>
              <span style={{
                background: '#FF3D3D22', color: '#FF3D3D',
                padding: '2px 8px', borderRadius: '4px',
                fontSize: '10px', fontWeight: 700, textAlign: 'center',
              }}>{evt.severity}</span>
              <span style={{ color: '#FFB800', fontFamily: 'monospace' }}>
                R:{evt.blast}
              </span>
              <span style={{ color: '#FF8C00', fontFamily: 'monospace', textAlign: 'right' }}>
                {evt.impact}
              </span>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
