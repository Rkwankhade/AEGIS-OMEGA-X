// AEGIS OMEGA X — GO TELEMETRY INGESTOR
// High-throughput event ingestion service
// MEGA-LAYER-1-PLANETARY-DIGITAL-TWIN/backend/go-services/telemetry-ingestor/main.go

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"sync"
	"sync/atomic"
	"syscall"
	"time"

	"github.com/IBM/sarama"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// ──────────────────────────────────────────────
// TYPES
// ──────────────────────────────────────────────

type TelemetryEvent struct {
	EventID    string                 `json:"event_id"`
	EventType  string                 `json:"event_type"`
	Source     string                 `json:"source"`
	EntityID   string                 `json:"entity_id"`
	AssetID    string                 `json:"asset_id,omitempty"`
	Timestamp  time.Time              `json:"timestamp"`
	Properties map[string]interface{} `json:"properties"`
	RiskScore  float64                `json:"risk_score,omitempty"`
}

type BatchResult struct {
	Processed int   `json:"processed"`
	Failed    int   `json:"failed"`
	DurationMs int64 `json:"duration_ms"`
}

// ──────────────────────────────────────────────
// METRICS
// ──────────────────────────────────────────────

var (
	eventsIngested = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "aegis_telemetry_events_ingested_total",
			Help: "Total telemetry events ingested",
		},
		[]string{"event_type", "source"},
	)
	ingestionDuration = prometheus.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "aegis_telemetry_ingestion_duration_seconds",
			Help:    "Duration of telemetry ingestion",
			Buckets: prometheus.DefBuckets,
		},
		[]string{"event_type"},
	)
	kafkaProducerErrors = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "aegis_kafka_producer_errors_total",
			Help: "Total Kafka producer errors",
		},
		[]string{"topic"},
	)
	batchSize = prometheus.NewHistogram(prometheus.HistogramOpts{
		Name:    "aegis_telemetry_batch_size",
		Help:    "Batch sizes for telemetry processing",
		Buckets: []float64{1, 10, 50, 100, 500, 1000},
	})
	activeWorkers = prometheus.NewGauge(prometheus.GaugeOpts{
		Name: "aegis_telemetry_active_workers",
		Help: "Number of active processing workers",
	})
)

func init() {
	prometheus.MustRegister(
		eventsIngested, ingestionDuration,
		kafkaProducerErrors, batchSize, activeWorkers,
	)
}

// ──────────────────────────────────────────────
// TOPIC ROUTER
// ──────────────────────────────────────────────

func routeTopic(eventType string) string {
	switch eventType {
	case "asset_scan", "asset_discovery", "asset_change":
		return "telemetry.assets"
	case "identity_change", "access_grant", "access_revoke", "login":
		return "telemetry.identities"
	case "cve_detected", "vulnerability_scan", "patch_applied":
		return "telemetry.vulnerabilities"
	case "config_change", "iac_scan", "secret_detected":
		return "telemetry.configurations"
	case "network_flow", "firewall_log", "dns_query":
		return "telemetry.network"
	case "control_change", "control_health", "alert":
		return "telemetry.controls"
	default:
		return "telemetry.assets"
	}
}

// ──────────────────────────────────────────────
// KAFKA PRODUCER POOL
// ──────────────────────────────────────────────

type ProducerPool struct {
	producers []sarama.SyncProducer
	mu        sync.Mutex
	index     int64
}

func NewProducerPool(brokers []string, poolSize int) (*ProducerPool, error) {
	cfg := sarama.NewConfig()
	cfg.Producer.RequiredAcks = sarama.WaitForLocal
	cfg.Producer.Compression = sarama.CompressionSnappy
	cfg.Producer.Flush.Frequency = 50 * time.Millisecond
	cfg.Producer.Flush.MaxMessages = 100
	cfg.Producer.Return.Successes = true
	cfg.Producer.Retry.Max = 3
	cfg.Net.DialTimeout = 10 * time.Second

	pool := &ProducerPool{producers: make([]sarama.SyncProducer, 0, poolSize)}
	for i := 0; i < poolSize; i++ {
		p, err := sarama.NewSyncProducer(brokers, cfg)
		if err != nil {
			return nil, fmt.Errorf("failed to create producer %d: %w", i, err)
		}
		pool.producers = append(pool.producers, p)
	}
	return pool, nil
}

func (pp *ProducerPool) Send(topic string, key string, value []byte) error {
	idx := atomic.AddInt64(&pp.index, 1) % int64(len(pp.producers))
	producer := pp.producers[idx]

	msg := &sarama.ProducerMessage{
		Topic: topic,
		Key:   sarama.StringEncoder(key),
		Value: sarama.ByteEncoder(value),
		Headers: []sarama.RecordHeader{
			{Key: []byte("source"), Value: []byte("aegis-telemetry-ingestor")},
			{Key: []byte("version"), Value: []byte("1.0.0")},
		},
	}

	_, _, err := producer.SendMessage(msg)
	if err != nil {
		kafkaProducerErrors.WithLabelValues(topic).Inc()
		return err
	}
	return nil
}

func (pp *ProducerPool) Close() {
	for _, p := range pp.producers {
		_ = p.Close()
	}
}

// ──────────────────────────────────────────────
// PROCESSING WORKER
// ──────────────────────────────────────────────

type Worker struct {
	id       int
	pool     *ProducerPool
	jobChan  <-chan TelemetryEvent
	doneChan chan<- struct{}
}

func (w *Worker) Run(ctx context.Context, wg *sync.WaitGroup) {
	defer wg.Done()
	activeWorkers.Inc()
	defer activeWorkers.Dec()

	log.Printf("[Worker %d] Started", w.id)
	for {
		select {
		case event, ok := <-w.jobChan:
			if !ok {
				log.Printf("[Worker %d] Job channel closed, stopping", w.id)
				return
			}
			w.process(event)
		case <-ctx.Done():
			log.Printf("[Worker %d] Context cancelled, stopping", w.id)
			return
		}
	}
}

func (w *Worker) process(event TelemetryEvent) {
	timer := prometheus.NewTimer(
		ingestionDuration.WithLabelValues(event.EventType),
	)
	defer timer.ObserveDuration()

	// Enrich event
	if event.EventID == "" {
		event.EventID = generateID()
	}
	if event.Timestamp.IsZero() {
		event.Timestamp = time.Now().UTC()
	}

	// Compute risk signal
	event.RiskScore = computeRiskSignal(event)

	// Serialize
	payload, err := json.Marshal(event)
	if err != nil {
		log.Printf("[Worker %d] Marshal error: %v", w.id, err)
		return
	}

	// Route to correct Kafka topic
	topic := routeTopic(event.EventType)
	key := event.EntityID
	if key == "" {
		key = event.AssetID
	}

	if err := w.pool.Send(topic, key, payload); err != nil {
		log.Printf("[Worker %d] Kafka error (topic=%s): %v", w.id, topic, err)
		return
	}

	eventsIngested.WithLabelValues(event.EventType, event.Source).Inc()
}

func computeRiskSignal(e TelemetryEvent) float64 {
	score := 0.2
	props := e.Properties

	if v, ok := props["privileged_account"].(bool); ok && v {
		score += 0.25
	}
	if v, ok := props["internet_facing"].(bool); ok && v {
		score += 0.15
	}
	if v, ok := props["known_bad_ip"].(bool); ok && v {
		score += 0.30
	}
	if v, ok := props["cve_exploit"].(bool); ok && v {
		score += 0.35
	}
	if v, ok := props["base_risk"].(float64); ok {
		score = (score + v) / 2.0
	}
	if score > 1.0 {
		score = 1.0
	}
	return score
}

func generateID() string {
	return fmt.Sprintf("%d-%d", time.Now().UnixNano(), time.Now().Nanosecond()%10000)
}

// ──────────────────────────────────────────────
// INGESTOR SERVICE
// ──────────────────────────────────────────────

type TelemetryIngestor struct {
	pool       *ProducerPool
	jobChan    chan TelemetryEvent
	workers    []*Worker
	workerCount int
	wg         sync.WaitGroup
	processed  atomic.Int64
}

func NewTelemetryIngestor(brokers []string, workerCount, poolSize, bufferSize int) (*TelemetryIngestor, error) {
	pool, err := NewProducerPool(brokers, poolSize)
	if err != nil {
		return nil, fmt.Errorf("producer pool error: %w", err)
	}

	ingestor := &TelemetryIngestor{
		pool:        pool,
		jobChan:     make(chan TelemetryEvent, bufferSize),
		workerCount: workerCount,
	}

	for i := 0; i < workerCount; i++ {
		w := &Worker{
			id:      i,
			pool:    pool,
			jobChan: ingestor.jobChan,
		}
		ingestor.workers = append(ingestor.workers, w)
	}

	return ingestor, nil
}

func (ti *TelemetryIngestor) Start(ctx context.Context) {
	log.Printf("[INGESTOR] Starting %d workers", ti.workerCount)
	for _, w := range ti.workers {
		ti.wg.Add(1)
		go w.Run(ctx, &ti.wg)
	}
}

func (ti *TelemetryIngestor) Ingest(event TelemetryEvent) {
	select {
	case ti.jobChan <- event:
		ti.processed.Add(1)
	default:
		log.Printf("[INGESTOR] Buffer full, dropping event: %s", event.EventID)
		kafkaProducerErrors.WithLabelValues("buffer_full").Inc()
	}
}

func (ti *TelemetryIngestor) IngestBatch(events []TelemetryEvent) BatchResult {
	start := time.Now()
	processed := 0
	failed := 0

	batchSize.Observe(float64(len(events)))

	for _, e := range events {
		select {
		case ti.jobChan <- e:
			processed++
		default:
			failed++
		}
	}

	return BatchResult{
		Processed:  processed,
		Failed:     failed,
		DurationMs: time.Since(start).Milliseconds(),
	}
}

func (ti *TelemetryIngestor) Shutdown() {
	log.Println("[INGESTOR] Shutting down...")
	close(ti.jobChan)
	ti.wg.Wait()
	ti.pool.Close()
	log.Printf("[INGESTOR] Shutdown complete. Total processed: %d", ti.processed.Load())
}

func (ti *TelemetryIngestor) Stats() map[string]interface{} {
	return map[string]interface{}{
		"total_processed": ti.processed.Load(),
		"buffer_capacity": cap(ti.jobChan),
		"buffer_used":     len(ti.jobChan),
		"worker_count":    ti.workerCount,
	}
}

// ──────────────────────────────────────────────
// HTTP SERVER
// ──────────────────────────────────────────────

func setupHTTPServer(ingestor *TelemetryIngestor) *http.ServeMux {
	mux := http.NewServeMux()

	// Health
	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(map[string]string{
			"status":  "operational",
			"service": "telemetry-ingestor",
			"version": "1.0.0",
		})
	})

	// Stats
	mux.HandleFunc("/stats", func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(ingestor.Stats())
	})

	// Single event ingest
	mux.HandleFunc("/ingest", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var event TelemetryEvent
		if err := json.NewDecoder(r.Body).Decode(&event); err != nil {
			http.Error(w, "invalid JSON", http.StatusBadRequest)
			return
		}
		ingestor.Ingest(event)
		w.WriteHeader(http.StatusAccepted)
		json.NewEncoder(w).Encode(map[string]string{"status": "accepted"})
	})

	// Batch ingest
	mux.HandleFunc("/ingest/batch", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var events []TelemetryEvent
		if err := json.NewDecoder(r.Body).Decode(&events); err != nil {
			http.Error(w, "invalid JSON", http.StatusBadRequest)
			return
		}
		if len(events) > 10000 {
			http.Error(w, "batch too large (max 10000)", http.StatusRequestEntityTooLarge)
			return
		}
		result := ingestor.IngestBatch(events)
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(result)
	})

	// Prometheus metrics
	mux.Handle("/metrics", promhttp.Handler())

	return mux
}

// ──────────────────────────────────────────────
// MAIN
// ──────────────────────────────────────────────

func main() {
	log.SetFlags(log.LstdFlags | log.Lshortfile)
	log.Println("AEGIS OMEGA X — Telemetry Ingestor v1.0.0")
	log.Println("==========================================")

	// Config from environment
	brokers := []string{getEnv("KAFKA_BROKERS", "localhost:9092")}
	workerCount := getEnvInt("WORKER_COUNT", 16)
	poolSize    := getEnvInt("PRODUCER_POOL_SIZE", 8)
	bufferSize  := getEnvInt("BUFFER_SIZE", 100000)
	port        := getEnv("PORT", "8010")

	log.Printf("Config: brokers=%v workers=%d pool=%d buffer=%d",
		brokers, workerCount, poolSize, bufferSize)

	// Create ingestor
	ingestor, err := NewTelemetryIngestor(brokers, workerCount, poolSize, bufferSize)
	if err != nil {
		log.Fatalf("Failed to create ingestor: %v", err)
	}

	// Start workers
	ctx, cancel := context.WithCancel(context.Background())
	ingestor.Start(ctx)

	// HTTP server
	mux := setupHTTPServer(ingestor)
	server := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
		IdleTimeout:  60 * time.Second,
	}

	// Graceful shutdown
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		log.Printf("[HTTP] Listening on :%s", port)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("HTTP server error: %v", err)
		}
	}()

	<-quit
	log.Println("[MAIN] Shutdown signal received")

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	if err := server.Shutdown(shutdownCtx); err != nil {
		log.Printf("[HTTP] Shutdown error: %v", err)
	}

	cancel()
	ingestor.Shutdown()
	log.Println("[MAIN] Clean exit")
}

func getEnv(key, fallback string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return fallback
}

func getEnvInt(key string, fallback int) int {
	if v := os.Getenv(key); v != "" {
		var n int
		fmt.Sscanf(v, "%d", &n)
		if n > 0 {
			return n
		}
	}
	return fallback
}

// go.mod:
// module github.com/aegis-omega-x/telemetry-ingestor
// go 1.22
// require (
//   github.com/IBM/sarama v1.42.1
//   github.com/prometheus/client_golang v1.18.0
// )
