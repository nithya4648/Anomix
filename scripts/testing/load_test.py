import asyncio
import os
import httpx
from datetime import datetime, timedelta
import argparse
import sys
from scripts.data import MetricSimulator


API_URL = "https://anomix-backend.onrender.com"
API_KEY = os.getenv("PULSEWATCH_API_KEY")


async def ingest_metric(client: httpx.AsyncClient, metric_name: str, value: float, timestamp: datetime):
    """Ingest a single metric"""
    
    payload = {
        "metric_name": metric_name,
        "value": value,
        "timestamp": timestamp.isoformat(),
        "labels": {"host": "server-1", "environment": "test"},
    }
    
    try:
        response = await client.post(
            f"{API_URL}/api/v1/metrics/ingest",
            json=payload,
            headers={"X-API-Key": API_KEY},
            timeout=10,
        )
        
        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return False
        
        return True
    
    except Exception as e:
        print(f"Error ingesting metric: {e}")
        return False


async def load_test(num_batches: int = 10, batch_size: int = 100):
    """Load test with metric ingestion"""
    
    simulator = MetricSimulator()
    metrics_data = simulator.get_all_metrics(num_points=num_batches * batch_size)
    
    start_time = datetime.utcnow() - timedelta(hours=24)
    
    async with httpx.AsyncClient() as client:
        total = 0
        errors = 0
        
        for batch_idx in range(num_batches):
            print(f"Processing batch {batch_idx + 1}/{num_batches}")
            
            tasks = []
            
            for i in range(batch_size):
                global_idx = batch_idx * batch_size + i
                timestamp = start_time + timedelta(minutes=i)
                
                for metric_name, data in metrics_data.items():
                    value, _ = data[global_idx]
                    
                    task = ingest_metric(client, metric_name, value, timestamp)
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            batch_errors = sum(1 for r in results if not r)
            
            total += len(results)
            errors += batch_errors
            
            print(f"  Ingested {len(results)} metrics ({batch_errors} errors)")
        
        print(f"\nTotal: {total} metrics ingested, {errors} errors")
        print(f"Success rate: {((total - errors) / total * 100):.2f}%")


def main():
    parser = argparse.ArgumentParser(description="Load test PulseWatch API")
    parser.add_argument("--batches", type=int, default=10, help="Number of batches")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(load_test(num_batches=args.batches, batch_size=args.batch_size))
    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
