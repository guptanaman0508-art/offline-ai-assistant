"""Unit and Smoke Tests for Model Benchmark components."""

import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.metrics import extract_generation_metrics, get_hardware_info
from src.benchmark import (
    load_benchmark_prompts,
    compute_summary_metrics,
    execute_single_prompt,
)


class TestBenchmarkComponents(unittest.TestCase):
    """Test suite ensuring benchmark orchestration and math work accurately."""

    def test_load_benchmark_prompts(self):
        prompts_file = Path(__file__).resolve().parent.parent / "data" / "benchmark_prompts.json"
        prompts = load_benchmark_prompts(prompts_file)
        self.assertGreaterEqual(len(prompts), 5)
        self.assertIn("id", prompts[0])
        self.assertIn("prompt", prompts[0])
        self.assertIn("reference_key_points", prompts[0])

    def test_extract_generation_metrics(self):
        mock_raw = MagicMock()
        mock_raw.eval_count = 100
        mock_raw.eval_duration = 2_000_000_000  # 2.0 seconds in ns
        mock_raw.load_duration = 500_000_000   # 0.5 seconds in ns
        mock_raw.prompt_eval_count = 25
        mock_raw.prompt_eval_duration = 100_000_000

        metrics = extract_generation_metrics(mock_raw)
        self.assertEqual(metrics["eval_count"], 100)
        self.assertEqual(metrics["eval_duration_s"], 2.0)
        self.assertEqual(metrics["load_duration_s"], 0.5)
        self.assertEqual(metrics["tokens_per_second"], 50.0)

    def test_get_hardware_info(self):
        hw = get_hardware_info()
        self.assertIn("os", hw)
        self.assertIn("total_ram_gb", hw)
        self.assertGreater(hw["total_ram_gb"], 0)

    def test_compute_summary_metrics(self):
        mock_raw_records = [
            # Warm-up (should be ignored in measured stats)
            {
                "model_name": "model_a",
                "run_type": "cold_warmup",
                "status": "SUCCESS",
                "latency_seconds": 5.0,
                "load_duration_s": 3.2,
                "tokens_per_second": 20.0,
                "peak_ram_mb": 1500.0,
            },
            # Measured run 1
            {
                "model_name": "model_a",
                "run_type": "measured",
                "status": "SUCCESS",
                "latency_seconds": 1.5,
                "load_duration_s": 0.1,
                "tokens_per_second": 40.0,
                "peak_ram_mb": 1600.0,
            },
            # Measured run 2
            {
                "model_name": "model_a",
                "run_type": "measured",
                "status": "SUCCESS",
                "latency_seconds": 2.5,
                "load_duration_s": 0.1,
                "tokens_per_second": 30.0,
                "peak_ram_mb": 1700.0,
            },
        ]

        summary = compute_summary_metrics(mock_raw_records, ["model_a"])
        self.assertEqual(len(summary), 1)
        s = summary[0]
        self.assertEqual(s["total_trials"], 2)
        self.assertEqual(s["successful_trials"], 2)
        self.assertEqual(s["success_rate_pct"], 100.0)
        self.assertEqual(s["median_latency_s"], 2.0)  # median of 1.5 and 2.5
        self.assertEqual(s["avg_tokens_per_second"], 35.0)  # mean of 40 and 30
        self.assertEqual(s["cold_start_load_s"], 3.2)  # pulled from warmup

    @patch("src.benchmark.get_ollama_memory_mb")
    def test_execute_single_prompt_failure_handling(self, mock_mem):
        mock_mem.return_value = 50.0
        mock_client = MagicMock()
        mock_client.chat.side_effect = RuntimeError("Model timeout")

        prompt = {"id": "p1", "category": "test", "prompt": "test?"}
        rec = execute_single_prompt(mock_client, "model_test", prompt, "measured", 1)

        self.assertEqual(rec["status"], "FAILED")
        self.assertIn("Model timeout", rec["error_message"])
        self.assertIsNone(rec["latency_seconds"])


if __name__ == "__main__":
    unittest.main()
