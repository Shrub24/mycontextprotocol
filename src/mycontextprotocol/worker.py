"""Omni-Worker for mycontextprotocol.

Processes ingestion tasks from Dragonfly queue.
Handles document chunking, embedding, and storage in LlamaIndex + LightRAG.

Runs as KEDA ScaledJob - scales based on queue depth.
"""

import asyncio
import json
import os
from typing import Any

import redis.asyncio as redis
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter

from mycontextprotocol.memory.llamaindex_store import create_index


class OmniWorker:
    def __init__(self):
        self.redis_host = os.getenv("DRAGONFLY_HOST", "dragonfly.queue.svc.cluster.local")
        self.redis_port = int(os.getenv("DRAGONFLY_PORT", "6379"))
        self.queue_name = "ingestion_queue"

        self.redis_client: Any = None
        self.llamaindex = None

    async def connect(self):
        """Connect to Dragonfly and initialize stores."""
        self.redis_client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            decode_responses=True,
        )

        self.llamaindex = create_index()

        print(f"✓ Connected to Dragonfly at {self.redis_host}:{self.redis_port}")
        print("✓ Initialized LlamaIndex store")

    async def process_task(self, task_data: dict[str, Any]) -> None:
        """Process a single ingestion task.

        Args:
            task_data: Task with 'content', 'metadata', 'stores' fields
        """
        content = task_data["content"]
        metadata = task_data.get("metadata", {})
        stores = task_data.get("stores", ["llamaindex", "lightrag"])

        print(f"Processing task: {len(content)} chars, stores: {stores}")

        if "llamaindex" in stores:
            await self._ingest_llamaindex(content, metadata)

        if "lightrag" in stores:
            await self._ingest_lightrag(content, metadata)

    async def _ingest_llamaindex(self, content: str, metadata: dict[str, Any]) -> None:
        """Ingest document to LlamaIndex."""
        doc = Document(text=content, metadata=metadata)

        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = splitter.get_nodes_from_documents([doc])

        if self.llamaindex is not None:
            self.llamaindex.insert_nodes(nodes)
            print(f"✓ Ingested to LlamaIndex: {len(nodes)} nodes")

    async def _ingest_lightrag(self, _content: str, _metadata: dict[str, Any]) -> None:
        """Ingest document to LightRAG."""
        print("⚠ LightRAG ingestion not yet implemented")

    async def run(self):
        """Main worker loop - process tasks from queue."""
        await self.connect()

        print(f"🔄 Listening on queue: {self.queue_name}")

        while True:
            try:
                if self.redis_client is None:
                    break

                result = await self.redis_client.blpop([self.queue_name], timeout=30)

                if result is None:
                    continue

                _, task_json = result
                task_data = json.loads(task_json)

                await self.process_task(task_data)
                print("✓ Task completed")

            except KeyboardInterrupt:
                print("\n⚠ Shutting down...")
                break
            except Exception as e:
                print(f"❌ Error processing task: {e}")
                await asyncio.sleep(1)

        if self.redis_client:
            await self.redis_client.close()


async def main():
    worker = OmniWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
