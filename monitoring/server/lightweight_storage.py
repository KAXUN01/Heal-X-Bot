"""
Lightweight JSON-based storage system to replace Elasticsearch
"""
import json
import os
import time
import threading
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class LightweightStorage:
    """JSON-based storage system to replace Elasticsearch functionality"""
    
    def __init__(self, data_dir: str = "/tmp/storage"):
        self.data_dir = data_dir
        self.lock = threading.RLock()
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self.data_dir, exist_ok=True)
    
    def _get_index_path(self, index_name: str) -> str:
        """Get the file path for an index"""
        return os.path.join(self.data_dir, f"{index_name}.jsonl")
    
    def index_document(self, index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """Index a document (equivalent to Elasticsearch index)"""
        try:
            with self.lock:
                # Generate document ID if not provided
                if not doc_id:
                    doc_id = f"{int(time.time() * 1000)}_{hash(str(document)) % 10000}"
                
                # Add metadata
                document_with_meta = {
                    "_id": doc_id,
                    "_timestamp": datetime.now().isoformat(),
                    **document
                }
                
                # Append to JSONL file
                index_path = self._get_index_path(index_name)
                with open(index_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(document_with_meta) + "\n")
                
                logger.debug(f"Indexed document {doc_id} to {index_name}")
                return doc_id
        except Exception as e:
            logger.error(f"Error indexing document to {index_name}: {e}")
            raise
    
    def search_documents(self, index_name: str, query: Optional[Dict[str, Any]] = None, 
                        size: int = 10, from_: int = 0) -> Dict[str, Any]:
        """Search documents (simplified Elasticsearch-like search)"""
        try:
            with self.lock:
                index_path = self._get_index_path(index_name)
                
                if not os.path.exists(index_path):
                    return {
                        "hits": {
                            "total": {"value": 0},
                            "hits": []
                        }
                    }
                
                documents = []
                with open(index_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                doc = json.loads(line.strip())
                                documents.append(doc)
                            except json.JSONDecodeError:
                                continue
                
                # Simple filtering (basic implementation)
                filtered_docs = documents
                if query:
                    filtered_docs = self._filter_documents(documents, query)
                
                # Pagination
                total = len(filtered_docs)
                start_idx = from_
                end_idx = min(from_ + size, total)
                page_docs = filtered_docs[start_idx:end_idx]
                
                # Format response similar to Elasticsearch
                hits = []
                for doc in page_docs:
                    hits.append({
                        "_id": doc.get("_id"),
                        "_source": {k: v for k, v in doc.items() if not k.startswith("_")},
                        "_score": 1.0  # Simple scoring
                    })
                
                return {
                    "hits": {
                        "total": {"value": total},
                        "hits": hits
                    }
                }
        except Exception as e:
            logger.error(f"Error searching {index_name}: {e}")
            return {
                "hits": {
                    "total": {"value": 0},
                    "hits": []
                }
            }
    
    def _filter_documents(self, documents: List[Dict], query: Dict[str, Any]) -> List[Dict]:
        """Simple document filtering"""
        filtered = documents
        
        # Handle simple term queries
        if "query" in query and "term" in query["query"]:
            term_query = query["query"]["term"]
            for field, value in term_query.items():
                filtered = [doc for doc in filtered if doc.get(field) == value]
        
        # Handle range queries
        if "query" in query and "range" in query["query"]:
            range_query = query["query"]["range"]
            for field, range_conditions in range_query.items():
                for condition, value in range_conditions.items():
                    if condition == "gte":
                        filtered = [doc for doc in filtered if doc.get(field, 0) >= value]
                    elif condition == "lte":
                        filtered = [doc for doc in filtered if doc.get(field, 0) <= value]
                    elif condition == "gt":
                        filtered = [doc for doc in filtered if doc.get(field, 0) > value]
                    elif condition == "lt":
                        filtered = [doc for doc in filtered if doc.get(field, 0) < value]
        
        return filtered
    
    def get_document(self, index_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        try:
            with self.lock:
                index_path = self._get_index_path(index_name)
                
                if not os.path.exists(index_path):
                    return None
                
                with open(index_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                doc = json.loads(line.strip())
                                if doc.get("_id") == doc_id:
                                    return doc
                            except json.JSONDecodeError:
                                continue
                
                return None
        except Exception as e:
            logger.error(f"Error getting document {doc_id} from {index_name}: {e}")
            return None
    
    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """Delete a document by ID"""
        try:
            with self.lock:
                index_path = self._get_index_path(index_name)
                
                if not os.path.exists(index_path):
                    return False
                
                # Read all documents, filter out the one to delete
                documents = []
                with open(index_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                doc = json.loads(line.strip())
                                if doc.get("_id") != doc_id:
                                    documents.append(doc)
                            except json.JSONDecodeError:
                                continue
                
                # Write back filtered documents
                with open(index_path, "w", encoding="utf-8") as f:
                    for doc in documents:
                        f.write(json.dumps(doc) + "\n")
                
                logger.debug(f"Deleted document {doc_id} from {index_name}")
                return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id} from {index_name}: {e}")
            return False
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get basic statistics for an index"""
        try:
            with self.lock:
                index_path = self._get_index_path(index_name)
                
                if not os.path.exists(index_path):
                    return {"count": 0, "size_bytes": 0}
                
                count = 0
                with open(index_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            count += 1
                
                size_bytes = os.path.getsize(index_path)
                
                return {
                    "count": count,
                    "size_bytes": size_bytes
                }
        except Exception as e:
            logger.error(f"Error getting stats for {index_name}: {e}")
            return {"count": 0, "size_bytes": 0}
    
    def cleanup_old_documents(self, index_name: str, days_to_keep: int = 7) -> int:
        """Clean up documents older than specified days"""
        try:
            with self.lock:
                index_path = self._get_index_path(index_name)
                
                if not os.path.exists(index_path):
                    return 0
                
                cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
                cutoff_timestamp = datetime.fromtimestamp(cutoff_time).isoformat()
                
                # Read all documents, filter out old ones
                documents = []
                deleted_count = 0
                
                with open(index_path, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip():
                            try:
                                doc = json.loads(line.strip())
                                doc_timestamp = doc.get("_timestamp", "")
                                if doc_timestamp >= cutoff_timestamp:
                                    documents.append(doc)
                                else:
                                    deleted_count += 1
                            except json.JSONDecodeError:
                                continue
                
                # Write back filtered documents
                with open(index_path, "w", encoding="utf-8") as f:
                    for doc in documents:
                        f.write(json.dumps(doc) + "\n")
                
                logger.info(f"Cleaned up {deleted_count} old documents from {index_name}")
                return deleted_count
        except Exception as e:
            logger.error(f"Error cleaning up {index_name}: {e}")
            return 0

# Global storage instance
storage = LightweightStorage()

# Convenience functions to match Elasticsearch-like interface
def index_document(index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None) -> str:
    """Index a document"""
    return storage.index_document(index_name, document, doc_id)

def search_documents(index_name: str, query: Optional[Dict[str, Any]] = None, 
                    size: int = 10, from_: int = 0) -> Dict[str, Any]:
    """Search documents"""
    return storage.search_documents(index_name, query, size, from_)

def get_document(index_name: str, doc_id: str) -> Optional[Dict[str, Any]]:
    """Get a document by ID"""
    return storage.get_document(index_name, doc_id)

def delete_document(index_name: str, doc_id: str) -> bool:
    """Delete a document by ID"""
    return storage.delete_document(index_name, doc_id)
