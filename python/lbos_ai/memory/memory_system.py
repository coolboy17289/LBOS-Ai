"""
Memory System for LBOS-AI
Implements hierarchical memory: working, episodic, and semantic memory
"""
import json
import pickle
import hashlib
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
import faiss
from sentence_transformers import SentenceTransformer

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class MemoryItem:
    """Base class for memory items"""
    id: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None

@dataclass
class WorkingMemoryItem(MemoryItem):
    """Short-term memory for current context"""
    session_id: str
    importance: float = 1.0

@dataclass
class EpisodicMemoryItem(MemoryItem):
    """Medium-term memory for specific events/interactions"""
    session_id: str
    event_type: str
    participants: List[str] = None

@dataclass
class SemanticMemoryItem(MemoryItem):
    """Long-term memory for knowledge and concepts"""
    category: str
    confidence: float = 1.0
    source: str = "observed"

class MemorySystem:
    def __init__(self, db_path: str = "./memory/lbos_memory.db",
                 embedding_model: str = "all-MiniLM-L6-v2"):
        """
        Initialize the memory system

        Args:
            db_path: Path to SQLite database for persistent storage
            embedding_model: Sentence transformer model for embeddings
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Initialize embedding model for semantic search
        self.embedding_model = SentenceTransformer(embedding_model)
        self.embedding_dim = self.embedding_model.get_sentence_embedding_dimension()

        # Initialize FAISS indices for fast similarity search
        self.working_index = None      # For recent items (small, frequently accessed)
        self.episodic_index = None     # For session-based items (medium term)
        self.semantic_index = None     # For knowledge base (large, persistent)

        # In-memory caches for quick access
        self.working_memory: Dict[str, WorkingMemoryItem] = {}
        self.episodic_memory: Dict[str, List[EpisodicMemoryItem]] = {}  # session_id -> items
        self.semantic_memory: Dict[str, SemanticMemoryItem] = {}       # concept_id -> item

        # Initialize database and indices
        self._init_database()
        self._load_indices()

        logger.info(f"Memory system initialized with db at {self.db_path}")

    def _init_database(self):
        """Initialize SQLite database for persistence"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Working memory table (session-based, short TTL)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS working_memory (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT,
                    importance REAL DEFAULT 1.0,
                    expires_at REAL
                )
            ''')

            # Episodic memory table (event-based, medium TTL)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    metadata TEXT,
                    participants TEXT
                )
            ''')

            # Semantic memory table (knowledge-based, long-term)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS semantic_memory (
                    id TEXT PRIMARY KEY,
                    concept TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    category TEXT,
                    confidence REAL DEFAULT 1.0,
                    source TEXT,
                    access_count INTEGER DEFAULT 0,
                    last_accessed REAL
                )
            ''')

            # Create indices for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_working_session ON working_session(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_working_expires ON working_memory(expires_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_episodic_session ON episodic_memory(session_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_episodic_type ON episodic_memory(event_type)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_semantic_concept ON semantic_memory(concept)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_semantic_category ON semantic_memory(category)')

            conn.commit()

    def _load_indices(self):
        """Load or initialize FAISS indices for similarity search"""
        # For simplicity, we'll rebuild indices on startup
        # In production, you'd save/load the indices to/from disk
        self.working_index = faiss.IndexFlatL2(self.embedding_dim)
        self.episodic_index = faiss.IndexFlatL2(self.embedding_dim)
        self.semantic_index = faiss.IndexFlatL2(self.embedding_dim)

        # Load existing data into memory and indices
        self._reload_from_database()

    def _reload_from_database(self):
        """Load existing data from database into memory structures"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Load working memory (only non-expired)
            cursor.execute('''
                SELECT id, session_id, content, timestamp, metadata, importance
                FROM working_memory
                WHERE expires_at > ? OR expires_at IS NULL
            ''', (datetime.now().timestamp(),))

            for row in cursor.fetchall():
                item = WorkingMemoryItem(
                    id=row[0],
                    session_id=row[1],
                    content=row[2],
                    timestamp=datetime.fromtimestamp(row[3]),
                    metadata=json.loads(row[4]) if row[4] else {},
                    importance=row[5]
                )
                self.working_memory[item.id] = item

                # Add to FAISS index
                if item.content:
                    embedding = self._get_embedding(item.content)
                    if embedding is not None:
                        self.working_index.add(np.array([embedding]))

            # Load episodic memory (last 30 days)
            cutoff = (datetime.now() - timedelta(days=30)).timestamp()
            cursor.execute('''
                SELECT id, session_id, event_type, content, timestamp, metadata, participants
                FROM episodic_memory
                WHERE timestamp > ?
            ''', (cutoff,))

            for row in cursor.fetchall():
                item = EpisodicMemoryItem(
                    id=row[0],
                    session_id=row[1],
                    event_type=row[2],
                    content=row[3],
                    timestamp=datetime.fromtimestamp(row[4]),
                    metadata=json.loads(row[5]) if row[5] else {},
                    participants=json.loads(row[6]) if row[6] else []
                )

                if item.session_id not in self.episodic_memory:
                    self.episodic_memory[item.session_id] = []
                self.episodic_memory[item.session_id].append(item)

                # Add to FAISS index
                if item.content:
                    embedding = self._get_embedding(item.content)
                    if embedding is not None:
                        self.episodic_index.add(np.array([embedding]))

            # Load semantic memory (all)
            cursor.execute('''
                SELECT id, concept, content, timestamp, category, confidence, source, access_count, last_accessed
                FROM semantic_memory
            ''')

            for row in cursor.fetchall():
                item = SemanticMemoryItem(
                    id=row[0],
                    content=row[2],
                    timestamp=datetime.fromtimestamp(row[3]),
                    metadata={
                        'concept': row[1],
                        'category': row[4],
                        'confidence': row[5],
                        'source': row[6]
                    }
                )
                self.semantic_memory[item.id] = item

                # Add to FAISS index
                if item.content:
                    embedding = self._get_embedding(item.content)
                    if embedding is not None:
                        self.semantic_index.add(np.array([embedding]))

            # Update access times in database
            cursor.execute('''
                UPDATE semantic_memory
                SET access_count = access_count + 1,
                    last_accessed = ?
            ''', (datetime.now().timestamp(),))
            conn.commit()

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get embedding for text using the sentence transformer"""
        try:
            if not text or not text.strip():
                return None
            embedding = self.embedding_model.encode([text])[0]
            return embedding.astype('float32')
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return None

    def _generate_id(self, content: str) -> str:
        """Generate unique ID for content"""
        timestamp = datetime.now().isoformat()
        hash_input = f"{content}_{timestamp}"
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    def add_to_working_memory(self, session_id: str, content: str,
                            metadata: Dict[str, Any] = None,
                            importance: float = 1.0,
                            ttl_seconds: int = 3600) -> str:
        """
        Add item to working memory (short-term)

        Args:
            session_id: Identifier for the current session
            content: Text content to store
            metadata: Additional metadata
            importance: Importance score (0.0-1.0) for retention
            ttl_seconds: Time to live in seconds

        Returns:
            ID of the stored item
        """
        item_id = self._generate_id(content)
        now = datetime.now()
        expires_at = (now + timedelta(seconds=ttl_seconds)).timestamp() if ttl_seconds > 0 else None

        item = WorkingMemoryItem(
            id=item_id,
            session_id=session_id,
            content=content,
            timestamp=now,
            metadata=metadata or {},
            importance=importance
        )

        # Store in memory
        self.working_memory[item_id] = item

        # Add to FAISS index
        embedding = self._get_embedding(content)
        if embedding is not None:
            self.working_index.add(np.array([embedding]))

        # Persist to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO working_memory
                (id, session_id, content, timestamp, metadata, importance, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id,
                session_id,
                content,
                now.timestamp(),
                json.dumps(metadata or {}),
                importance,
                expires_at
            ))
            conn.commit()

        logger.debug(f"Added to working memory: {item_id} (session: {session_id})")
        return item_id

    def add_to_episodic_memory(self, session_id: str, event_type: str, content: str,
                             metadata: Dict[str, Any] = None,
                             participants: List[str] = None) -> str:
        """
        Add item to episodic memory (medium-term)

        Args:
            session_id: Identifier for the session
            event_type: Type of event (e.g., 'conversation', 'task_completion')
            content: Description of what happened
            metadata: Additional context
            participants: List of participants involved

        Returns:
            ID of the stored item
        """
        item_id = self._generate_id(content)
        now = datetime.now()

        item = EpisodicMemoryItem(
            id=item_id,
            session_id=session_id,
            event_type=event_type,
            content=content,
            timestamp=now,
            metadata=metadata or {},
            participants=participants or []
        )

        # Store in memory cache
        if session_id not in self.episodic_memory:
            self.episodic_memory[session_id] = []
        self.episodic_memory[session_id].append(item)

        # Add to FAISS index
        embedding = self._get_embedding(content)
        if embedding is not None:
            self.episodic_index.add(np.array([embedding]))

        # Persist to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO episodic_memory
                (id, session_id, event_type, content, timestamp, metadata, participants)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id,
                session_id,
                event_type,
                content,
                now.timestamp(),
                json.dumps(metadata or {}),
                json.dumps(participants or [])
            ))
            conn.commit()

        logger.debug(f"Added to episodic memory: {item_id} (session: {session_id}, event: {event_type})")
        return item_id

    def add_to_semantic_memory(self, concept: str, content: str,
                             category: str = "general",
                             confidence: float = 1.0,
                             source: str = "observed") -> str:
        """
        Add item to semantic memory (long-term knowledge)

        Args:
            concept: The concept or entity this memory represents
            content: Detailed description or definition
            category: Broad category (e.g., 'person', 'place', 'fact')
            confidence: Confidence in accuracy (0.0-1.0)
            source: Source of this knowledge

        Returns:
            ID of the stored item
        """
        item_id = self._generate_id(f"{concept}_{content}")
        now = datetime.now()

        item = SemanticMemoryItem(
            id=item_id,
            content=content,
            timestamp=now,
            metadata={
                'concept': concept,
                'category': category,
                'confidence': confidence,
                'source': source
            }
        )

        # Store in memory cache
        self.semantic_memory[item_id] = item

        # Add to FAISS index
        embedding = self._get_embedding(content)
        if embedding is not None:
            self.semantic_index.add(np.array([embedding]))

        # Persist to database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO semantic_memory
                (id, concept, content, timestamp, category, confidence, source)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                item_id,
                concept,
                content,
                now.timestamp(),
                category,
                confidence,
                source
            ))
            conn.commit()

        logger.debug(f"Added to semantic memory: {item_id} (concept: {concept})")
        return item_id

    def retrieve_relevant_memories(self, query: str,
                                 memory_types: List[str] = None,
                                 limit: int = 5,
                                 min_similarity: float = 0.7) -> Dict[str, List[Dict]]:
        """
        Retrieve relevant memories across all memory types

        Args:
            query: Text query to search for
            memory_types: List of memory types to search ('working', 'episodic', 'semantic')
            limit: Maximum number of results per type
            min_similarity: Minimum similarity threshold (0.0-1.0)

        Returns:
            Dictionary with memory types as keys and lists of matching items as values
        """
        if memory_types is None:
            memory_types = ['working', 'episodic', 'semantic']

        if not query.strip():
            return {mt: [] for mt in memory_types}

        # Get query embedding
        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return {mt: [] for mt in memory_types}

        query_vector = np.array([query_embedding]).astype('float32')
        results = {}

        # Search working memory
        if 'working' in memory_types and len(self.working_memory) > 0:
            try:
                distances, indices = self.working_index.search(
                    np.array([query_embedding]),
                    min(limit * 2, len(self.working_memory))
                )

                working_results = []
                id_list = list(self.working_memory.keys())
                for i, idx in enumerate(indices[0]):
                    if idx < len(id_list) and distances[0][i] < (2 - 2 * min_similarity):  # Convert distance to similarity
                        item_id = id_list[idx]
                        item = self.working_memory[item_id]
                        similarity = 1 - (distances[0][i] / 2)  # Convert L2 distance to approximate cosine

                        if similarity >= min_similarity:
                            working_results.append({
                                **asdict(item),
                                'similarity': float(similarity),
                                'memory_type': 'working'
                            })

                results['working'] = sorted(working_results, key=lambda x: x['similarity'], reverse=True)[:limit]
            except Exception as e:
                logger.error(f"Error searching working memory: {e}")
                results['working'] = []

        # Search episodic memory
        if 'episodic' in memory_types and self.episodic_index.ntotal > 0:
            try:
                distances, indices = self.episodic_index.search(
                    np.array([query_embedding]),
                    min(limit * 2, self.episodic_index.ntotal)
                )

                episodic_results = []
                # Flatten episodic memory for indexing
                all_episodic = []
                for session_items in self.episodic_memory.values():
                    all_episodic.extend(session_items)

                for i, idx in enumerate(indices[0]):
                    if idx < len(all_episodic) and distances[0][i] < (2 - 2 * min_similarity):
                        item = all_episodic[idx]
                        similarity = 1 - (distances[0][i] / 2)

                        if similarity >= min_similarity:
                            episodic_results.append({
                                **asdict(item),
                                'similarity': float(similarity),
                                'memory_type': 'episodic'
                            })

                results['episodic'] = sorted(episodic_results, key=lambda x: x['similarity'], reverse=True)[:limit]
            except Exception as e:
                logger.error(f"Error searching episodic memory: {e}")
                results['episodic'] = []

        # Search semantic memory
        if 'semantic' in memory_types and self.semantic_index.ntotal > 0:
            try:
                distances, indices = self.semantic_index.search(
                    np.array([query_embedding]),
                    min(limit * 2, self.semantic_index.ntotal)
                )

                semantic_results = []
                id_list = list(self.semantic_memory.keys())
                for i, idx in enumerate(indices[0]):
                    if idx < len(id_list) and distances[0][i] < (2 - 2 * min_similarity):
                        item_id = id_list[idx]
                        item = self.semantic_memory[item_id]
                        similarity = 1 - (distances[0][i] / 2)

                        if similarity >= min_similarity:
                            # Update access statistics
                            self._update_access_time(item_id)

                            semantic_results.append({
                                **asdict(item),
                                'similarity': float(similarity),
                                'memory_type': 'semantic'
                            })

                results['semantic'] = sorted(semantic_results, key=lambda x: x['similarity'], reverse=True)[:limit]
            except Exception as e:
                logger.error(f"Error searching semantic memory: {e}")
                results['semantic'] = []

        return results

    def _update_access_time(self, item_id: str):
        """Update access time and count for semantic memory item"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE semantic_memory
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE id = ?
            ''', (datetime.now().timestamp(), item_id))
            conn.commit()

    def get_recent_interactions(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent interactions for a session"""
        if session_id not in self.episodic_memory:
            return []

        # Sort by timestamp descending and return most recent
        sorted_items = sorted(
            self.episodic_memory[session_id],
            key=lambda x: x.timestamp,
            reverse=True
        )

        return [
            {
                **asdict(item),
                'memory_type': 'episodic'
            }
            for item in sorted_items[:limit]
        ]

    def consolidate_memories(self):
        """
        Consolidate memories: move important items from working to episodic,
        and significant episodic items to semantic memory
        """
        now = datetime.now()

        # Promote important working memory items to episodic
        to_promote = []
        for item_id, item in list(self.working_memory.items()):
            # Promote if high importance or older than threshold
            if item.importance > 0.8 or (now - item.timestamp).total_seconds() > 1800:  # 30 minutes
                to_promote.append((item_id, item))

        for item_id, item in to_promote:
            # Convert working memory item to episodic
            episodic_item = EpisodicMemoryItem(
                id=self._generate_id(item.content),
                session_id=item.session_id,
                event_type="working_memory_promotion",
                content=item.content,
                timestamp=item.timestamp,
                metadata={
                    **item.metadata,
                    'promoted_from': 'working_memory',
                    'original_importance': item.importance
                }
            )

            self.add_to_episodic_memory(
                episodic_item.session_id,
                episodic_item.event_type,
                episodic_item.content,
                episodic_item.metadata
            )

            # Remove from working memory
            del self.working_memory[item_id]

        # Consolidate episodic to semantic for highly accessed or important items
        # This would typically involve more sophisticated importance scoring

        logger.info("Memory consolidation completed")

    def cleanup_expired(self):
        """Remove expired memories from all stores"""
        now = datetime.now().timestamp()

        # Clean working memory (based on expires_at)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM working_memory WHERE expires_at < ? AND expires_at IS NOT NULL', (now,))
            expired_working = cursor.rowcount

            # Optional: cleanup very old episodic memory (> 1 year)
            cutoff = (datetime.now() - timedelta(days=365)).timestamp()
            cursor.execute('DELETE FROM episodic_memory WHERE timestamp < ?', (cutoff,))
            expired_episodic = cursor.rowcount

            conn.commit()

        # Reload indices to reflect changes
        self._reload_from_database()

        logger.info(f"Cleaned up {expired_working} expired working memory items and {expired_episodic} old episodic items")

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the memory system"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # Working memory count
            cursor.execute('SELECT COUNT(*) FROM working_memory WHERE expires_at > ? OR expires_at IS NULL',
                         (datetime.now().timestamp(),))
            working_count = cursor.fetchone()[0]

            # Episodic memory count
            cursor.execute('SELECT COUNT(*) FROM episodic_memory')
            episodic_count = cursor.fetchone()[0]

            # Semantic memory count
            cursor.execute('SELECT COUNT(*) FROM semantic_memory')
            semantic_count = cursor.fetchone()[0]

            # Average importance in working memory
            cursor.execute('SELECT AVG(importance) FROM working_memory WHERE expires_at > ? OR expires_at IS NULL',
                         (datetime.now().timestamp(),))
            avg_importance = cursor.fetchone()[0] or 0

            # Most accessed semantic items
            cursor.execute('''
                SELECT concept, access_count
                FROM semantic_memory
                ORDER BY access_count DESC
                LIMIT 5
            ''')
            top_concepts = cursor.fetchall()

        return {
            'working_memory': {
                'count': working_count,
                'average_importance': round(avg_importance, 3)
            },
            'episodic_memory': {
                'count': episodic_count
            },
            'semantic_memory': {
                'count': semantic_count,
                'top_concepts': [{'concept': c, 'access_count': a} for c, a in top_concepts]
            },
            'total_items': working_count + episodic_count + semantic_count
        }

# Global memory instance
memory_system = None

def get_memory_system() -> MemorySystem:
    """Get or create the global memory system instance"""
    global memory_system
    if memory_system is None:
        memory_system = MemorySystem()
    return memory_system

def init_memory_system(db_path: str = "./memory/lbos_memory.db") -> MemorySystem:
    """Initialize the memory system with custom path"""
    global memory_system
    memory_system = MemorySystem(db_path)
    return memory_system

# Example usage
if __name__ == "__main__":
    # Initialize memory system
    mem = MemorySystem("./test_memory.db")

    # Add some test memories
    mem.add_to_working_memory("session_1", "User asked about the weather today",
                            {"topic": "weather"}, importance=0.7)

    mem.add_to_episodic_memory("session_1", "user_query",
                             "User asked: What's the weather like in New York?",
                             {"intent": "get_weather", "location": "New York"})

    mem.add_to_semantic_memory("New York City",
                             "New York City is the most populous city in the United States",
                             "geographical_entity", 0.95, "knowledge_base")

    # Search for relevant memories
    results = mem.retrieve_relevant_memories("What is the weather in NYC?")
    print("Search results:", json.dumps(results, indent=2, default=str))

    # Get statistics
    stats = mem.get_statistics()
    print("Memory statistics:", json.dumps(stats, indent=2))