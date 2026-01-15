"""Omni-Worker for mycontextprotocol.

Processes ingestion tasks from Dragonfly queue.
Handles document chunking, embedding, and storage in LlamaIndex + LightRAG.

Runs as KEDA ScaledJob - scales based on queue depth.
"""

import asyncio
import json
import signal
from typing import Any

import redis.asyncio as redis
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from mem0 import Memory

from mycontextprotocol.config import Settings
from mycontextprotocol.memory.lightrag_client import insert_document
from mycontextprotocol.memory.llamaindex_store import create_index
from mycontextprotocol.memory.mem0_client import get_mem0_config
from mycontextprotocol.worker_llm import DocumentExtractor


class OmniWorker:
    def __init__(self):
        self.settings = Settings.model_validate({})
        self.queue_name = "ingestion_queue"
        self.dead_letter_queue = "ingestion_dlq"

        self.redis_client: Any = None
        self.llamaindex = None
        self.mem0: Memory | None = None
        self.extractor: DocumentExtractor | None = None
        self.shutdown = False

    async def connect(self):
        """Connect to Dragonfly and initialize stores."""
        self.redis_client = redis.Redis(
            host=self.settings.dragonfly_host,
            port=self.settings.dragonfly_port,
            password=self.settings.dragonfly_password if self.settings.dragonfly_password else None,
            decode_responses=True,
        )

        self.llamaindex = create_index()
        self.mem0 = Memory.from_config(get_mem0_config())
        self.extractor = DocumentExtractor(self.settings)

        print(
            f"✓ Connected to Dragonfly at {self.settings.dragonfly_host}:{self.settings.dragonfly_port}"
        )
        print("✓ Initialized LlamaIndex store")
        print("✓ Initialized Mem0 client")
        print("✓ Initialized LLM extractor")

    async def process_task(self, task_data: dict[str, Any]) -> None:
        """Process a single ingestion task.

        Args:
            task_data: Task with 'content', 'metadata', 'stores' fields
        """
        content = task_data["content"]
        metadata = task_data.get("metadata", {})
        stores = task_data.get("stores", ["llamaindex", "lightrag"])
        user_id = metadata.get("user_id")

        print(f"Processing task: {len(content)} chars, stores: {stores}")

        if self.extractor:
            extracted = await self.extractor.extract(content, user_id)
            metadata["summary"] = extracted.summary
            metadata["entities"] = extracted.entities
            metadata["topics"] = extracted.topics
            print(f"✓ Extracted: {len(extracted.facts)} facts, {len(extracted.entities)} entities")

        if "llamaindex" in stores:
            await self._ingest_llamaindex(content, metadata)

        if "lightrag" in stores:
            await self._ingest_lightrag(content, metadata)

        if user_id and self.mem0 and self.extractor:
            extracted = await self.extractor.extract(content, user_id)
            await self._extract_user_facts(extracted, user_id)

    async def _ingest_llamaindex(self, content: str, metadata: dict[str, Any]) -> None:
        """Ingest document to LlamaIndex."""
        doc = Document(text=content, metadata=metadata)

        splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = splitter.get_nodes_from_documents([doc])

        if self.llamaindex is not None:
            self.llamaindex.insert_nodes(nodes)
            print(f"✓ Ingested to LlamaIndex: {len(nodes)} nodes")

    async def _ingest_lightrag(self, content: str, metadata: dict[str, Any]) -> None:
        """Ingest document to LightRAG."""
        try:
            track_id = await insert_document(content, metadata)
            print(f"✓ Ingested to LightRAG: track_id={track_id}")
        except Exception as e:
            print(f"❌ LightRAG ingestion failed: {e}")
            raise

    async def _extract_user_facts(self, extracted: Any, user_id: str) -> None:
        """Extract user-specific facts using Mem0."""
        try:
            if self.mem0 is None:
                return

            confidence_threshold = 0.6
            for fact in extracted.facts:
                if fact.confidence > confidence_threshold:
                    self.mem0.add(fact.fact, user_id=user_id, metadata={"category": fact.category})

            print(f"✓ Extracted {len(extracted.facts)} user facts for user_id={user_id}")
        except Exception as e:
            print(f"❌ Mem0 fact extraction failed: {e}")
            raise

    def setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""

        def handle_shutdown(signum: int, _frame: Any) -> None:
            print(f"\n⚠ Received signal {signum}, shutting down gracefully...")
            self.shutdown = True

        signal.signal(signal.SIGTERM, handle_shutdown)
        signal.signal(signal.SIGINT, handle_shutdown)

    async def run(self):
        """Main worker loop - process tasks from queue."""
        await self.connect()
        self.setup_signal_handlers()

        print(f"🔄 Listening on queue: {self.queue_name}")

        while not self.shutdown:
            try:
                if self.redis_client is None:
                    break

                result = await self.redis_client.blpop([self.queue_name], timeout=5)

                if result is None:
                    continue

                _, task_json = result
                task_data = json.loads(task_json)

                try:
                    await self.process_task(task_data)
                    print("✓ Task completed")
                except Exception as task_error:
                    print(f"❌ Task processing failed: {task_error}")
                    if self.redis_client:
                        await self.redis_client.rpush(self.dead_letter_queue, task_json)
                        print(f"➡ Moved to dead-letter queue: {self.dead_letter_queue}")

            except Exception as e:
                print(f"❌ Worker error: {e}")
                await asyncio.sleep(1)

        print("⚠ Shutdown complete")
        if self.redis_client:
            await self.redis_client.close()


async def main():
    worker = OmniWorker()
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
