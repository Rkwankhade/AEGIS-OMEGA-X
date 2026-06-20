// AEGIS OMEGA X — MEGA LAYER 1
// PLANETARY DIGITAL TWIN — SIMULATION CORE (Rust)
// pdt-simulation-core/src/main.rs

use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::{Mutex, RwLock};
use tokio::time;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};

// ──────────────────────────────────────────────
// TYPES
// ──────────────────────────────────────────────

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum SimStatus {
    Nominal,
    Degraded,
    Compromised,
    Failed,
    Recovering,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AssetState {
    pub asset_id: String,
    pub entity_id: String,
    pub status: SimStatus,
    pub risk_score: f64,
    pub last_updated: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EntityState {
    pub entity_id: String,
    pub name: String,
    pub global_risk: f64,
    pub compromised_assets: u64,
    pub total_assets: u64,
    pub status: SimStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CascadeEvent {
    pub event_id: String,
    pub origin_asset_id: String,
    pub propagation_path: Vec<String>,
    pub affected_assets: Vec<String>,
    pub severity: f64,
    pub tick_started: u64,
    pub tick_contained: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SimulationTick {
    pub tick_id: String,
    pub tick_number: u64,
    pub timestamp: DateTime<Utc>,
    pub global_risk_score: f64,
    pub total_assets: u64,
    pub compromised_assets: u64,
    pub active_cascades: u64,
    pub tick_duration_ms: f64,
}

// ──────────────────────────────────────────────
// SIMULATION STATE
// ──────────────────────────────────────────────

pub struct PlanetarySimulationState {
    pub tick: u64,
    pub assets: HashMap<String, AssetState>,
    pub entities: HashMap<String, EntityState>,
    pub active_cascades: Vec<CascadeEvent>,
    pub relationship_graph: HashMap<String, Vec<String>>,  // adjacency
    pub tick_history: Vec<SimulationTick>,
}

impl PlanetarySimulationState {
    pub fn new() -> Self {
        Self {
            tick: 0,
            assets: HashMap::new(),
            entities: HashMap::new(),
            active_cascades: Vec::new(),
            relationship_graph: HashMap::new(),
            tick_history: Vec::new(),
        }
    }

    pub fn global_risk_score(&self) -> f64 {
        if self.assets.is_empty() {
            return 0.0;
        }
        let total: f64 = self.assets.values().map(|a| a.risk_score).sum();
        total / self.assets.len() as f64
    }

    pub fn compromised_count(&self) -> u64 {
        self.assets
            .values()
            .filter(|a| a.status == SimStatus::Compromised)
            .count() as u64
    }
}

// ──────────────────────────────────────────────
// CASCADE PROPAGATION ENGINE
// ──────────────────────────────────────────────

pub struct CascadeEngine;

impl CascadeEngine {
    /// Propagate a cascade event one tick forward.
    /// Uses a simple BFS over the relationship graph with
    /// stochastic propagation probability based on risk scores.
    pub fn propagate(
        state: &mut PlanetarySimulationState,
        cascade: &mut CascadeEvent,
        propagation_probability: f64,
    ) {
        let mut newly_affected: Vec<String> = Vec::new();

        for asset_id in cascade.affected_assets.clone().iter() {
            if let Some(neighbors) = state.relationship_graph.get(asset_id).cloned() {
                for neighbor_id in neighbors {
                    if cascade.affected_assets.contains(&neighbor_id) {
                        continue;
                    }
                    // Stochastic propagation
                    let roll: f64 = rand_f64();
                    if let Some(neighbor) = state.assets.get(&neighbor_id) {
                        let adjusted_prob = propagation_probability * neighbor.risk_score;
                        if roll < adjusted_prob {
                            newly_affected.push(neighbor_id.clone());
                        }
                    }
                }
            }
        }

        for asset_id in &newly_affected {
            if let Some(asset) = state.assets.get_mut(asset_id) {
                asset.status = SimStatus::Compromised;
                asset.last_updated = Utc::now();
            }
            cascade.propagation_path.push(asset_id.clone());
            cascade.affected_assets.push(asset_id.clone());
        }
    }
}

/// Simple LCG pseudo-random for simulation (replace with proper RNG in production)
fn rand_f64() -> f64 {
    use std::time::SystemTime;
    let nanos = SystemTime::now()
        .duration_since(SystemTime::UNIX_EPOCH)
        .unwrap_or(Duration::from_nanos(0))
        .subsec_nanos();
    (nanos as f64 % 1000.0) / 1000.0
}

// ──────────────────────────────────────────────
// RISK SCORING ENGINE
// ──────────────────────────────────────────────

pub struct RiskEngine;

impl RiskEngine {
    /// Recompute risk scores for all assets each tick.
    /// Factors: base vulnerability, exposure, cascade proximity, identity risk.
    pub fn recompute_all(state: &mut PlanetarySimulationState) {
        // Collect cascade-affected sets first
        let cascade_affected: std::collections::HashSet<String> = state
            .active_cascades
            .iter()
            .flat_map(|c| c.affected_assets.clone())
            .collect();

        for (asset_id, asset) in state.assets.iter_mut() {
            let cascade_factor = if cascade_affected.contains(asset_id) {
                0.3
            } else {
                0.0
            };

            let exposure_factor = if asset.status == SimStatus::Compromised {
                0.5
            } else {
                0.0
            };

            // Clamp risk to [0.0, 1.0]
            asset.risk_score = (asset.risk_score + cascade_factor + exposure_factor).min(1.0);
        }
    }
}

// ──────────────────────────────────────────────
// SIMULATION ORCHESTRATOR
// ──────────────────────────────────────────────

pub struct PlanetarySimulationOrchestrator {
    pub state: Arc<RwLock<PlanetarySimulationState>>,
    pub tick_interval_ms: u64,
    pub running: Arc<Mutex<bool>>,
}

impl PlanetarySimulationOrchestrator {
    pub fn new(tick_interval_ms: u64) -> Self {
        Self {
            state: Arc::new(RwLock::new(PlanetarySimulationState::new())),
            tick_interval_ms,
            running: Arc::new(Mutex::new(false)),
        }
    }

    pub async fn start(&self) {
        {
            let mut running = self.running.lock().await;
            *running = true;
        }

        let state_ref = self.state.clone();
        let running_ref = self.running.clone();
        let interval = self.tick_interval_ms;

        tokio::spawn(async move {
            let mut ticker = time::interval(Duration::from_millis(interval));
            loop {
                ticker.tick().await;

                let running = running_ref.lock().await;
                if !*running {
                    break;
                }
                drop(running);

                let start = Instant::now();
                let mut state = state_ref.write().await;
                state.tick += 1;

                // 1. Propagate all active cascades
                let mut cascades = state.active_cascades.clone();
                for cascade in cascades.iter_mut() {
                    CascadeEngine::propagate(&mut state, cascade, 0.15);
                }
                state.active_cascades = cascades;

                // 2. Recompute risk scores
                RiskEngine::recompute_all(&mut state);

                // 3. Record tick
                let duration_ms = start.elapsed().as_secs_f64() * 1000.0;
                let tick_record = SimulationTick {
                    tick_id: Uuid::new_v4().to_string(),
                    tick_number: state.tick,
                    timestamp: Utc::now(),
                    global_risk_score: state.global_risk_score(),
                    total_assets: state.assets.len() as u64,
                    compromised_assets: state.compromised_count(),
                    active_cascades: state.active_cascades.len() as u64,
                    tick_duration_ms: duration_ms,
                };

                state.tick_history.push(tick_record.clone());

                // Keep only last 1000 ticks in memory
                if state.tick_history.len() > 1000 {
                    state.tick_history.remove(0);
                }

                println!(
                    "[TICK {}] risk={:.3} compromised={} cascades={} duration={:.2}ms",
                    tick_record.tick_number,
                    tick_record.global_risk_score,
                    tick_record.compromised_assets,
                    tick_record.active_cascades,
                    tick_record.tick_duration_ms,
                );
            }
        });
    }

    pub async fn stop(&self) {
        let mut running = self.running.lock().await;
        *running = false;
    }

    pub async fn inject_cascade(&self, origin_asset_id: String, severity: f64) {
        let mut state = self.state.write().await;
        let cascade = CascadeEvent {
            event_id: Uuid::new_v4().to_string(),
            origin_asset_id: origin_asset_id.clone(),
            propagation_path: vec![origin_asset_id.clone()],
            affected_assets: vec![origin_asset_id.clone()],
            severity,
            tick_started: state.tick,
            tick_contained: None,
        };
        if let Some(asset) = state.assets.get_mut(&origin_asset_id) {
            asset.status = SimStatus::Compromised;
        }
        state.active_cascades.push(cascade);
    }
}

// ──────────────────────────────────────────────
// MAIN ENTRYPOINT
// ──────────────────────────────────────────────

#[tokio::main]
async fn main() {
    println!("AEGIS OMEGA X — Planetary Digital Twin Simulation Core");
    println!("=========================================================");

    let orchestrator = PlanetarySimulationOrchestrator::new(1000); // 1 tick/second

    // Seed some test assets
    {
        let mut state = orchestrator.state.write().await;

        // Add 5 test assets
        for i in 0..5 {
            let asset_id = format!("asset-{:03}", i);
            state.assets.insert(asset_id.clone(), AssetState {
                asset_id: asset_id.clone(),
                entity_id: "ent-001".to_string(),
                status: SimStatus::Nominal,
                risk_score: 0.1 + (i as f64 * 0.1),
                last_updated: Utc::now(),
            });

            // Build a linear chain dependency
            if i > 0 {
                let prev = format!("asset-{:03}", i - 1);
                state.relationship_graph
                    .entry(prev)
                    .or_insert_with(Vec::new)
                    .push(asset_id);
            }
        }

        println!("Seeded {} assets", state.assets.len());
    }

    // Start simulation
    orchestrator.start().await;

    // After 3 ticks, inject a cascade from asset-000
    time::sleep(Duration::from_millis(3100)).await;
    println!("\n[INJECT] Cascade from asset-000 (severity=0.9)\n");
    orchestrator.inject_cascade("asset-000".to_string(), 0.9).await;

    // Run for 10 more ticks
    time::sleep(Duration::from_millis(10000)).await;
    orchestrator.stop().await;

    // Print final state
    let state = orchestrator.state.read().await;
    println!("\n=== FINAL STATE ===");
    println!("Total ticks: {}", state.tick);
    println!("Global risk: {:.3}", state.global_risk_score());
    println!("Compromised assets: {}", state.compromised_count());
    for (id, asset) in &state.assets {
        println!("  {} => {:?} risk={:.3}", id, asset.status, asset.risk_score);
    }
}

// ──────────────────────────────────────────────
// Cargo.toml dependencies:
// [dependencies]
// tokio = { version = "1", features = ["full"] }
// serde = { version = "1", features = ["derive"] }
// serde_json = "1"
// uuid = { version = "1", features = ["v4"] }
// chrono = { version = "0.4", features = ["serde"] }
