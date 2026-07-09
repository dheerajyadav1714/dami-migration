INSERT INTO dami_data_v3.gpu_benchmarks 
  (benchmark_id, method, rows_processed, processing_seconds, speedup_factor, gpu_device, platform, job_id, details_json, created_at)
VALUES 
  ('bench-colab-t4', 'cudf_gpu', 100000, 0.847, 28.5, 'NVIDIA T4', 'google_colab', 'colab-session-001', '{"framework": "cudf", "cuda": "12.2"}', '2026-07-08T15:00:00'),
  ('bench-colab-cpu', 'pandas_cpu', 100000, 24.14, 1.0, 'None (CPU)', 'google_colab', 'colab-session-001', '{"mode": "cpu_baseline"}', '2026-07-08T15:00:00')
