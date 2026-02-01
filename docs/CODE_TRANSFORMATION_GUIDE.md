# LegalMind: Code Transformation Guide

This document provides the exact code changes needed to transform the legacy procurement system into LegalMind.

---

## Table of Contents

1. [Backend Configuration](#1-backend-configuration)
2. [Gemini Service Implementation](#2-gemini-service-implementation)
3. [Firestore Service Implementation](#3-firestore-service-implementation)
4. [Storage Service Implementation](#4-storage-service-implementation)
5. [Tool Implementations](#5-tool-implementations)
6. [Agent Definitions](#6-agent-definitions)
7. [Chat Manager Implementation](#7-chat-manager-implementation)
8. [API Endpoints](#8-api-endpoints)
9. [Frontend Changes](#9-frontend-changes)

---

## 1. Backend Configuration

### 1.1 New `requirements.txt`

```txt
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-dotenv==1.0.0
pydantic==2.5.3

# Google Cloud
google-generativeai==0.4.0
google-cloud-firestore==2.14.0
google-cloud-storage==2.14.0
firebase-admin==6.4.0

# Document Processing
python-docx==1.1.0
pypdf==3.17.4
markdown==3.5.2

# Utilities
aiohttp==3.9.1
tenacity==8.2.3
python-multipart==0.0.6
```

### 1.2 New `config/settings.py`

```python
"""Configuration settings for LegalMind."""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_name: str = "LegalMind"
    app_env: str = "development"
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"
    
    # Gemini API
    gemini_api_key: str
    gemini_model: str = "gemini-2.0-flash"
    
    # Google Cloud
    google_cloud_project: str
    google_application_credentials: str = ""
    
    # Firestore
    firestore_database: str = "(default)"
    
    # Cloud Storage
    gcs_bucket_name: str = "legalmind-storage"
    gcs_contract_prefix: str = "contract-pdfs"
    gcs_document_prefix: str = "generated-documents"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


def get_gemini_model_name() -> str:
    """Get the Gemini model name."""
    return get_settings().gemini_model


def get_gcs_bucket_name() -> str:
    """Get the GCS bucket name."""
    return get_settings().gcs_bucket_name
```

### 1.3 New `.env.example`

```env
# LegalMind Environment Variables

# Gemini API
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.0-flash

# Google Cloud Project
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Firestore
FIRESTORE_DATABASE=(default)

# Cloud Storage
GCS_BUCKET_NAME=legalmind-storage
GCS_CONTRACT_PREFIX=contract-pdfs
GCS_DOCUMENT_PREFIX=generated-documents

# Application
APP_ENV=development
LOG_LEVEL=INFO
CORS_ORIGINS=http://localhost:3000,https://legalmind.web.app
```

---

## 2. Gemini Service Implementation

### 2.1 `services/gemini_service.py`

```python
"""Gemini API service for LegalMind."""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from functools import lru_cache

import google.generativeai as genai
from google.generativeai.types import GenerationConfig, Tool, FunctionDeclaration

from config.settings import get_settings


class GeminiService:
    """Service for interacting with Gemini API."""
    
    def __init__(self):
        """Initialize Gemini service."""
        settings = get_settings()
        genai.configure(api_key=settings.gemini_api_key)
        self.model_name = settings.gemini_model
        self._tool_handlers: Dict[str, Callable] = {}
    
    def register_tool_handler(self, tool_name: str, handler: Callable):
        """Register a handler function for a tool.
        
        Args:
            tool_name: Name of the tool
            handler: Function to call when tool is invoked
        """
        self._tool_handlers[tool_name] = handler
    
    def create_model(
        self,
        system_instruction: str,
        tools: Optional[List[Dict]] = None,
        enable_search: bool = False
    ) -> genai.GenerativeModel:
        """Create a Gemini model with specified configuration.
        
        Args:
            system_instruction: System prompt for the model
            tools: List of tool definitions
            enable_search: Whether to enable Google Search grounding
            
        Returns:
            Configured GenerativeModel instance
        """
        model_tools = []
        
        # Add function calling tools
        if tools:
            function_declarations = []
            for tool in tools:
                func_decl = FunctionDeclaration(
                    name=tool["name"],
                    description=tool["description"],
                    parameters=tool.get("parameters", {})
                )
                function_declarations.append(func_decl)
            model_tools.append(Tool(function_declarations=function_declarations))
        
        # Add Google Search grounding
        if enable_search:
            # Gemini 2.0 has built-in search grounding
            model_tools.append(Tool(google_search_retrieval={}))
        
        model = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=system_instruction,
            tools=model_tools if model_tools else None,
            generation_config=GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=8192,
            )
        )
        
        return model
    
    async def generate_with_tools(
        self,
        model: genai.GenerativeModel,
        prompt: str,
        chat_history: Optional[List[Dict]] = None,
        max_tool_calls: int = 10
    ) -> Dict[str, Any]:
        """Generate response with automatic tool execution.
        
        Args:
            model: The Gemini model to use
            prompt: User prompt
            chat_history: Previous conversation history
            max_tool_calls: Maximum number of tool calls to allow
            
        Returns:
            Dict with response text, tool calls, and citations
        """
        # Start or continue chat
        if chat_history:
            chat = model.start_chat(history=chat_history)
        else:
            chat = model.start_chat()
        
        # Send message
        response = await asyncio.to_thread(chat.send_message, prompt)
        
        tool_calls_made = []
        iterations = 0
        
        # Handle tool calls in a loop
        while response.candidates[0].content.parts:
            has_function_call = False
            
            for part in response.candidates[0].content.parts:
                if hasattr(part, 'function_call') and part.function_call:
                    has_function_call = True
                    func_call = part.function_call
                    tool_name = func_call.name
                    tool_args = dict(func_call.args) if func_call.args else {}
                    
                    tool_calls_made.append({
                        "name": tool_name,
                        "args": tool_args
                    })
                    
                    # Execute the tool
                    if tool_name in self._tool_handlers:
                        try:
                            result = await self._execute_tool(tool_name, tool_args)
                            tool_result = json.dumps(result) if isinstance(result, (dict, list)) else str(result)
                        except Exception as e:
                            tool_result = json.dumps({"error": str(e)})
                    else:
                        tool_result = json.dumps({"error": f"Unknown tool: {tool_name}"})
                    
                    # Send tool result back
                    response = await asyncio.to_thread(
                        chat.send_message,
                        genai.protos.Content(
                            parts=[genai.protos.Part(
                                function_response=genai.protos.FunctionResponse(
                                    name=tool_name,
                                    response={"result": tool_result}
                                )
                            )]
                        )
                    )
            
            if not has_function_call:
                break
            
            iterations += 1
            if iterations >= max_tool_calls:
                break
        
        # Extract final response text
        response_text = ""
        citations = []
        
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'text') and part.text:
                response_text += part.text
        
        # Extract citations from grounding metadata if available
        if hasattr(response.candidates[0], 'grounding_metadata'):
            grounding = response.candidates[0].grounding_metadata
            if hasattr(grounding, 'grounding_chunks'):
                for chunk in grounding.grounding_chunks:
                    if hasattr(chunk, 'web'):
                        citations.append({
                            "title": chunk.web.title if hasattr(chunk.web, 'title') else "",
                            "uri": chunk.web.uri if hasattr(chunk.web, 'uri') else ""
                        })
        
        return {
            "text": response_text,
            "tool_calls": tool_calls_made,
            "citations": citations,
            "history": chat.history
        }
    
    async def _execute_tool(self, tool_name: str, args: Dict) -> Any:
        """Execute a registered tool handler.
        
        Args:
            tool_name: Name of the tool to execute
            args: Arguments to pass to the tool
            
        Returns:
            Tool execution result
        """
        handler = self._tool_handlers.get(tool_name)
        if not handler:
            raise ValueError(f"No handler registered for tool: {tool_name}")
        
        # Check if handler is async
        if asyncio.iscoroutinefunction(handler):
            return await handler(**args)
        else:
            return await asyncio.to_thread(handler, **args)
    
    async def simple_generate(
        self,
        prompt: str,
        system_instruction: str = "",
        enable_search: bool = False
    ) -> str:
        """Simple text generation without tools.
        
        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            enable_search: Whether to enable search grounding
            
        Returns:
            Generated text
        """
        model = self.create_model(
            system_instruction=system_instruction,
            enable_search=enable_search
        )
        
        response = await asyncio.to_thread(model.generate_content, prompt)
        return response.text


@lru_cache()
def get_gemini_service() -> GeminiService:
    """Get cached Gemini service instance."""
    return GeminiService()
```

---

## 3. Firestore Service Implementation

### 3.1 `services/firestore_service.py`

```python
"""Firestore service for LegalMind."""

import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from functools import lru_cache

from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

from config.settings import get_settings


class FirestoreService:
    """Service for Firestore database operations."""
    
    def __init__(self):
        """Initialize Firestore client."""
        settings = get_settings()
        
        # Initialize with project ID
        if settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
        
        self.db = firestore.Client(
            project=settings.google_cloud_project,
            database=settings.firestore_database
        )
    
    # ==================== CONTRACTS ====================
    
    async def create_contract(self, contract_data: Dict) -> str:
        """Create a new contract document.
        
        Args:
            contract_data: Contract data dictionary
            
        Returns:
            Created contract ID
        """
        contract_data["created_at"] = datetime.utcnow()
        contract_data["updated_at"] = datetime.utcnow()
        
        doc_ref = self.db.collection("contracts").document()
        doc_ref.set(contract_data)
        
        return doc_ref.id
    
    async def get_contract(self, contract_id: str) -> Optional[Dict]:
        """Get a contract by ID.
        
        Args:
            contract_id: Contract document ID
            
        Returns:
            Contract data or None
        """
        doc = self.db.collection("contracts").document(contract_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None
    
    async def update_contract(self, contract_id: str, updates: Dict) -> bool:
        """Update a contract.
        
        Args:
            contract_id: Contract document ID
            updates: Fields to update
            
        Returns:
            True if successful
        """
        updates["updated_at"] = datetime.utcnow()
        self.db.collection("contracts").document(contract_id).update(updates)
        return True
    
    async def delete_contract(self, contract_id: str) -> bool:
        """Delete a contract and its subcollections.
        
        Args:
            contract_id: Contract document ID
            
        Returns:
            True if successful
        """
        contract_ref = self.db.collection("contracts").document(contract_id)
        
        # Delete clauses subcollection
        clauses = contract_ref.collection("clauses").stream()
        for clause in clauses:
            clause.reference.delete()
        
        # Delete main document
        contract_ref.delete()
        return True
    
    async def list_contracts(
        self,
        user_id: Optional[str] = None,
        contract_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List contracts with optional filters.
        
        Args:
            user_id: Filter by user
            contract_type: Filter by type
            status: Filter by status
            limit: Maximum results
            
        Returns:
            List of contracts
        """
        query = self.db.collection("contracts")
        
        if user_id:
            query = query.where(filter=FieldFilter("created_by", "==", user_id))
        if contract_type:
            query = query.where(filter=FieldFilter("contract_type", "==", contract_type))
        if status:
            query = query.where(filter=FieldFilter("status", "==", status))
        
        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)
        
        contracts = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            contracts.append(data)
        
        return contracts
    
    # ==================== CLAUSES ====================
    
    async def add_clause(self, contract_id: str, clause_data: Dict) -> str:
        """Add a clause to a contract.
        
        Args:
            contract_id: Parent contract ID
            clause_data: Clause data
            
        Returns:
            Created clause ID
        """
        clause_data["created_at"] = datetime.utcnow()
        
        doc_ref = (
            self.db.collection("contracts")
            .document(contract_id)
            .collection("clauses")
            .document()
        )
        doc_ref.set(clause_data)
        
        return doc_ref.id
    
    async def get_clauses(self, contract_id: str) -> List[Dict]:
        """Get all clauses for a contract.
        
        Args:
            contract_id: Contract ID
            
        Returns:
            List of clauses
        """
        clauses = []
        docs = (
            self.db.collection("contracts")
            .document(contract_id)
            .collection("clauses")
            .order_by("page_number")
            .stream()
        )
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            clauses.append(data)
        
        return clauses
    
    # ==================== SESSIONS ====================
    
    async def create_session(self, session_data: Dict) -> str:
        """Create a new chat session.
        
        Args:
            session_data: Session data
            
        Returns:
            Created session ID
        """
        session_data["created_at"] = datetime.utcnow()
        session_data["last_activity"] = datetime.utcnow()
        session_data["status"] = "active"
        
        doc_ref = self.db.collection("sessions").document()
        doc_ref.set(session_data)
        
        return doc_ref.id
    
    async def get_session(self, session_id: str) -> Optional[Dict]:
        """Get a session by ID.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None
        """
        doc = self.db.collection("sessions").document(session_id).get()
        if doc.exists:
            data = doc.to_dict()
            data["id"] = doc.id
            return data
        return None
    
    async def update_session_activity(self, session_id: str):
        """Update session last activity timestamp.
        
        Args:
            session_id: Session ID
        """
        self.db.collection("sessions").document(session_id).update({
            "last_activity": datetime.utcnow()
        })
    
    async def add_message(self, session_id: str, message_data: Dict) -> str:
        """Add a message to a session.
        
        Args:
            session_id: Session ID
            message_data: Message data
            
        Returns:
            Created message ID
        """
        message_data["timestamp"] = datetime.utcnow()
        
        doc_ref = (
            self.db.collection("sessions")
            .document(session_id)
            .collection("messages")
            .document()
        )
        doc_ref.set(message_data)
        
        # Update session activity
        await self.update_session_activity(session_id)
        
        return doc_ref.id
    
    async def get_messages(
        self,
        session_id: str,
        limit: int = 100
    ) -> List[Dict]:
        """Get messages for a session.
        
        Args:
            session_id: Session ID
            limit: Maximum messages to return
            
        Returns:
            List of messages
        """
        messages = []
        docs = (
            self.db.collection("sessions")
            .document(session_id)
            .collection("messages")
            .order_by("timestamp")
            .limit(limit)
            .stream()
        )
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            messages.append(data)
        
        return messages
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """List chat sessions.
        
        Args:
            user_id: Filter by user
            limit: Maximum results
            
        Returns:
            List of sessions
        """
        query = self.db.collection("sessions")
        
        if user_id:
            query = query.where(filter=FieldFilter("user_id", "==", user_id))
        
        query = query.order_by("last_activity", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)
        
        sessions = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            sessions.append(data)
        
        return sessions
    
    # ==================== THINKING LOGS ====================
    
    async def log_thinking(self, log_data: Dict) -> str:
        """Log agent thinking process.
        
        Args:
            log_data: Thinking log data
            
        Returns:
            Created log ID
        """
        log_data["timestamp"] = datetime.utcnow()
        
        doc_ref = self.db.collection("thinking_logs").document()
        doc_ref.set(log_data)
        
        return doc_ref.id
    
    async def get_thinking_logs(
        self,
        session_id: Optional[str] = None,
        conversation_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get thinking logs.
        
        Args:
            session_id: Filter by session
            conversation_id: Filter by conversation
            limit: Maximum results
            
        Returns:
            List of thinking logs
        """
        query = self.db.collection("thinking_logs")
        
        if session_id:
            query = query.where(filter=FieldFilter("session_id", "==", session_id))
        if conversation_id:
            query = query.where(filter=FieldFilter("conversation_id", "==", conversation_id))
        
        query = query.order_by("timestamp", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)
        
        logs = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            logs.append(data)
        
        return logs
    
    # ==================== DOCUMENTS ====================
    
    async def create_document_record(self, doc_data: Dict) -> str:
        """Create a document record.
        
        Args:
            doc_data: Document metadata
            
        Returns:
            Created document ID
        """
        doc_data["created_at"] = datetime.utcnow()
        
        doc_ref = self.db.collection("documents").document()
        doc_ref.set(doc_data)
        
        return doc_ref.id
    
    async def get_documents(
        self,
        session_id: Optional[str] = None,
        contract_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """Get generated documents.
        
        Args:
            session_id: Filter by session
            contract_id: Filter by contract
            limit: Maximum results
            
        Returns:
            List of documents
        """
        query = self.db.collection("documents")
        
        if session_id:
            query = query.where(filter=FieldFilter("session_id", "==", session_id))
        if contract_id:
            query = query.where(filter=FieldFilter("contract_id", "==", contract_id))
        
        query = query.order_by("created_at", direction=firestore.Query.DESCENDING)
        query = query.limit(limit)
        
        documents = []
        for doc in query.stream():
            data = doc.to_dict()
            data["id"] = doc.id
            documents.append(data)
        
        return documents
    
    # ==================== COMPLIANCE RULES ====================
    
    async def get_compliance_rules(self, regulation: str) -> List[Dict]:
        """Get compliance rules for a regulation.
        
        Args:
            regulation: Regulation name (GDPR, HIPAA, etc.)
            
        Returns:
            List of compliance rules
        """
        rules = []
        docs = (
            self.db.collection("compliance_rules")
            .where(filter=FieldFilter("regulation", "==", regulation))
            .stream()
        )
        
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            rules.append(data)
        
        return rules
    
    # ==================== DASHBOARD STATS ====================
    
    async def get_dashboard_stats(self, user_id: Optional[str] = None) -> Dict:
        """Get dashboard statistics.
        
        Args:
            user_id: Filter by user
            
        Returns:
            Statistics dictionary
        """
        contracts_query = self.db.collection("contracts")
        if user_id:
            contracts_query = contracts_query.where(
                filter=FieldFilter("created_by", "==", user_id)
            )
        
        # Count contracts by status
        all_contracts = list(contracts_query.stream())
        
        stats = {
            "total_contracts": len(all_contracts),
            "active_contracts": sum(1 for c in all_contracts if c.to_dict().get("status") == "active"),
            "draft_contracts": sum(1 for c in all_contracts if c.to_dict().get("status") == "draft"),
            "high_risk_contracts": sum(
                1 for c in all_contracts 
                if c.to_dict().get("overall_risk_score", 0) >= 51
            ),
            "compliance_issues": sum(
                1 for c in all_contracts 
                if c.to_dict().get("compliance_status") in ["partial", "non-compliant"]
            )
        }
        
        # Get risk distribution
        risk_levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        for contract in all_contracts:
            score = contract.to_dict().get("overall_risk_score", 0)
            if score <= 25:
                risk_levels["low"] += 1
            elif score <= 50:
                risk_levels["medium"] += 1
            elif score <= 75:
                risk_levels["high"] += 1
            else:
                risk_levels["critical"] += 1
        
        stats["risk_distribution"] = risk_levels
        
        return stats


@lru_cache()
def get_firestore_service() -> FirestoreService:
    """Get cached Firestore service instance."""
    return FirestoreService()
```

---

## 4. Storage Service Implementation

### 4.1 `services/storage_service.py`

```python
"""Cloud Storage service for LegalMind."""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional, BinaryIO
from functools import lru_cache

from google.cloud import storage
from google.cloud.storage import Blob

from config.settings import get_settings


class StorageService:
    """Service for Google Cloud Storage operations."""
    
    def __init__(self):
        """Initialize storage client."""
        settings = get_settings()
        
        if settings.google_application_credentials:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.google_application_credentials
        
        self.client = storage.Client(project=settings.google_cloud_project)
        self.bucket_name = settings.gcs_bucket_name
        self.contract_prefix = settings.gcs_contract_prefix
        self.document_prefix = settings.gcs_document_prefix
        
        # Get or create bucket
        self.bucket = self._get_or_create_bucket()
    
    def _get_or_create_bucket(self) -> storage.Bucket:
        """Get existing bucket or create new one.
        
        Returns:
            Storage bucket
        """
        try:
            bucket = self.client.get_bucket(self.bucket_name)
        except Exception:
            bucket = self.client.create_bucket(self.bucket_name)
        return bucket
    
    def upload_contract_pdf(
        self,
        file_content: bytes,
        filename: str,
        user_id: str,
        contract_id: str
    ) -> str:
        """Upload a contract PDF.
        
        Args:
            file_content: PDF file bytes
            filename: Original filename
            user_id: User ID
            contract_id: Contract ID
            
        Returns:
            GCS URI of uploaded file
        """
        blob_path = f"{self.contract_prefix}/{user_id}/{contract_id}/{filename}"
        blob = self.bucket.blob(blob_path)
        
        blob.upload_from_string(
            file_content,
            content_type="application/pdf"
        )
        
        return f"gs://{self.bucket_name}/{blob_path}"
    
    def upload_document(
        self,
        file_content: bytes,
        filename: str,
        session_id: str,
        document_id: str,
        content_type: str = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ) -> str:
        """Upload a generated document.
        
        Args:
            file_content: Document bytes
            filename: Filename
            session_id: Session ID
            document_id: Document ID
            content_type: MIME type
            
        Returns:
            GCS URI of uploaded file
        """
        blob_path = f"{self.document_prefix}/{session_id}/{document_id}/{filename}"
        blob = self.bucket.blob(blob_path)
        
        blob.upload_from_string(file_content, content_type=content_type)
        
        return f"gs://{self.bucket_name}/{blob_path}"
    
    def get_download_url(
        self,
        gcs_uri: str,
        expiration_minutes: int = 60
    ) -> str:
        """Get a signed download URL for a file.
        
        Args:
            gcs_uri: GCS URI (gs://bucket/path)
            expiration_minutes: URL expiration time
            
        Returns:
            Signed download URL
        """
        # Parse GCS URI
        if gcs_uri.startswith("gs://"):
            path = gcs_uri.replace(f"gs://{self.bucket_name}/", "")
        else:
            path = gcs_uri
        
        blob = self.bucket.blob(path)
        
        url = blob.generate_signed_url(
            version="v4",
            expiration=timedelta(minutes=expiration_minutes),
            method="GET"
        )
        
        return url
    
    def download_file(self, gcs_uri: str) -> bytes:
        """Download a file from GCS.
        
        Args:
            gcs_uri: GCS URI
            
        Returns:
            File content bytes
        """
        if gcs_uri.startswith("gs://"):
            path = gcs_uri.replace(f"gs://{self.bucket_name}/", "")
        else:
            path = gcs_uri
        
        blob = self.bucket.blob(path)
        return blob.download_as_bytes()
    
    def delete_file(self, gcs_uri: str) -> bool:
        """Delete a file from GCS.
        
        Args:
            gcs_uri: GCS URI
            
        Returns:
            True if successful
        """
        if gcs_uri.startswith("gs://"):
            path = gcs_uri.replace(f"gs://{self.bucket_name}/", "")
        else:
            path = gcs_uri
        
        blob = self.bucket.blob(path)
        blob.delete()
        return True
    
    def list_files(self, prefix: str) -> list:
        """List files with a given prefix.
        
        Args:
            prefix: Path prefix
            
        Returns:
            List of blob names
        """
        blobs = self.bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]


@lru_cache()
def get_storage_service() -> StorageService:
    """Get cached storage service instance."""
    return StorageService()
```

---

## 5. Tool Implementations

### 5.1 `tools/__init__.py`

```python
"""Gemini tools for LegalMind agents."""

from .contract_tools import ContractTools, CONTRACT_TOOL_DEFINITIONS
from .clause_tools import ClauseTools, CLAUSE_TOOL_DEFINITIONS
from .compliance_tools import ComplianceTools, COMPLIANCE_TOOL_DEFINITIONS
from .risk_tools import RiskTools, RISK_TOOL_DEFINITIONS
from .document_tools import DocumentTools, DOCUMENT_TOOL_DEFINITIONS
from .logging_tools import LoggingTools, LOGGING_TOOL_DEFINITIONS

# Combine all tool definitions
ALL_TOOL_DEFINITIONS = (
    CONTRACT_TOOL_DEFINITIONS +
    CLAUSE_TOOL_DEFINITIONS +
    COMPLIANCE_TOOL_DEFINITIONS +
    RISK_TOOL_DEFINITIONS +
    DOCUMENT_TOOL_DEFINITIONS +
    LOGGING_TOOL_DEFINITIONS
)

__all__ = [
    "ContractTools",
    "ClauseTools", 
    "ComplianceTools",
    "RiskTools",
    "DocumentTools",
    "LoggingTools",
    "ALL_TOOL_DEFINITIONS",
    "CONTRACT_TOOL_DEFINITIONS",
    "CLAUSE_TOOL_DEFINITIONS",
    "COMPLIANCE_TOOL_DEFINITIONS",
    "RISK_TOOL_DEFINITIONS",
    "DOCUMENT_TOOL_DEFINITIONS",
    "LOGGING_TOOL_DEFINITIONS"
]
```

### 5.2 `tools/contract_tools.py`

```python
"""Contract database tools for Gemini agents."""

import json
from typing import Dict, List, Optional
from services.firestore_service import get_firestore_service


CONTRACT_TOOL_DEFINITIONS = [
    {
        "name": "get_contract_by_id",
        "description": "Retrieves a contract document from the database by its ID. Returns contract metadata, parties, dates, and associated clauses.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The unique identifier of the contract"
                }
            },
            "required": ["contract_id"]
        }
    },
    {
        "name": "search_contracts",
        "description": "Searches contracts by various criteria including client name, contract type, date range, and status.",
        "parameters": {
            "type": "object",
            "properties": {
                "client_name": {
                    "type": "string",
                    "description": "Name of the client/party to search for"
                },
                "contract_type": {
                    "type": "string",
                    "description": "Type of contract (NDA, MSA, Employment, Lease, etc.)"
                },
                "date_from": {
                    "type": "string",
                    "description": "Start date for date range filter (YYYY-MM-DD)"
                },
                "date_to": {
                    "type": "string",
                    "description": "End date for date range filter (YYYY-MM-DD)"
                },
                "status": {
                    "type": "string",
                    "enum": ["active", "expired", "draft", "terminated"],
                    "description": "Contract status filter"
                }
            }
        }
    },
    {
        "name": "save_contract",
        "description": "Saves a new contract or updates an existing one with parsed contract data.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "Contract ID (optional for new contracts)"
                },
                "contract_data": {
                    "type": "object",
                    "description": "Contract data including type, parties, dates, etc."
                },
                "session_id": {
                    "type": "string",
                    "description": "Current session ID"
                }
            },
            "required": ["contract_data", "session_id"]
        }
    }
]


class ContractTools:
    """Tool implementations for contract operations."""
    
    def __init__(self):
        self.firestore = get_firestore_service()
    
    async def get_contract_by_id(self, contract_id: str) -> Dict:
        """Get contract by ID with clauses.
        
        Args:
            contract_id: Contract ID
            
        Returns:
            Contract data with clauses
        """
        contract = await self.firestore.get_contract(contract_id)
        if not contract:
            return {"error": f"Contract {contract_id} not found"}
        
        # Get clauses
        clauses = await self.firestore.get_clauses(contract_id)
        contract["clauses"] = clauses
        
        return contract
    
    async def search_contracts(
        self,
        client_name: Optional[str] = None,
        contract_type: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict]:
        """Search contracts with filters.
        
        Args:
            client_name: Client name filter
            contract_type: Contract type filter
            date_from: Start date filter
            date_to: End date filter
            status: Status filter
            
        Returns:
            List of matching contracts
        """
        contracts = await self.firestore.list_contracts(
            contract_type=contract_type,
            status=status
        )
        
        # Additional filtering for client_name (would need Firestore query enhancement)
        if client_name:
            contracts = [
                c for c in contracts
                if any(
                    client_name.lower() in (p.get("name", "") or "").lower()
                    for p in c.get("parties", [])
                )
            ]
        
        return contracts
    
    async def save_contract(
        self,
        contract_data: Dict,
        session_id: str,
        contract_id: Optional[str] = None
    ) -> Dict:
        """Save or update a contract.
        
        Args:
            contract_data: Contract data
            session_id: Session ID
            contract_id: Optional existing contract ID
            
        Returns:
            Saved contract data
        """
        if contract_id:
            # Update existing
            await self.firestore.update_contract(contract_id, contract_data)
            return {"contract_id": contract_id, "status": "updated"}
        else:
            # Create new
            new_id = await self.firestore.create_contract(contract_data)
            return {"contract_id": new_id, "status": "created"}
```

### 5.3 `tools/logging_tools.py`

```python
"""Logging tools for agent thinking process."""

import json
from typing import Dict, Optional
from services.firestore_service import get_firestore_service


LOGGING_TOOL_DEFINITIONS = [
    {
        "name": "log_agent_thinking",
        "description": "Logs the agent's reasoning process for transparency and auditability. Call this at each major step of your analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "agent_name": {
                    "type": "string",
                    "description": "Name of the agent logging (e.g., CONTRACT_PARSER_AGENT)"
                },
                "thinking_stage": {
                    "type": "string",
                    "description": "Stage of thinking (e.g., analysis_start, clause_extraction, risk_assessment)"
                },
                "thought_content": {
                    "type": "string",
                    "description": "Detailed description of the agent's reasoning at this stage"
                },
                "thinking_stage_output": {
                    "type": "string",
                    "description": "Specific outputs or intermediate results from this stage"
                },
                "session_id": {
                    "type": "string",
                    "description": "Current session ID"
                },
                "conversation_id": {
                    "type": "string",
                    "description": "Current conversation ID within the session"
                }
            },
            "required": ["agent_name", "thinking_stage", "thought_content", "session_id"]
        }
    },
    {
        "name": "get_session_history",
        "description": "Retrieves the conversation history for context.",
        "parameters": {
            "type": "object",
            "properties": {
                "session_id": {
                    "type": "string",
                    "description": "Session ID to get history for"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of messages to retrieve",
                    "default": 50
                }
            },
            "required": ["session_id"]
        }
    }
]


class LoggingTools:
    """Tool implementations for logging operations."""
    
    def __init__(self):
        self.firestore = get_firestore_service()
    
    async def log_agent_thinking(
        self,
        agent_name: str,
        thinking_stage: str,
        thought_content: str,
        session_id: str,
        thinking_stage_output: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Dict:
        """Log agent thinking process.
        
        Args:
            agent_name: Name of the agent
            thinking_stage: Current stage
            thought_content: Reasoning content
            session_id: Session ID
            thinking_stage_output: Stage-specific output
            conversation_id: Conversation ID
            
        Returns:
            Log confirmation
        """
        log_data = {
            "agent_name": agent_name,
            "thinking_stage": thinking_stage,
            "thought_content": thought_content,
            "session_id": session_id,
            "conversation_id": conversation_id,
            "thinking_stage_output": thinking_stage_output,
            "model_name": "gemini-2.0-flash"
        }
        
        log_id = await self.firestore.log_thinking(log_data)
        
        return {
            "status": "logged",
            "log_id": log_id,
            "agent_name": agent_name,
            "thinking_stage": thinking_stage
        }
    
    async def get_session_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> Dict:
        """Get session conversation history.
        
        Args:
            session_id: Session ID
            limit: Max messages
            
        Returns:
            Session history
        """
        messages = await self.firestore.get_messages(session_id, limit=limit)
        
        return {
            "session_id": session_id,
            "message_count": len(messages),
            "messages": messages
        }
```

---

## 6. Agent Definitions

### 6.1 `agents/agent_definitions.py` (Complete Replacement)

```python
"""Agent definitions for LegalMind."""

# Agent names
CONTRACT_PARSER_AGENT = "CONTRACT_PARSER_AGENT"
LEGAL_RESEARCH_AGENT = "LEGAL_RESEARCH_AGENT"
COMPLIANCE_CHECKER_AGENT = "COMPLIANCE_CHECKER_AGENT"
RISK_ASSESSMENT_AGENT = "RISK_ASSESSMENT_AGENT"
LEGAL_MEMO_AGENT = "LEGAL_MEMO_AGENT"
ASSISTANT_AGENT = "ASSISTANT_AGENT"

# All agents list
ALL_AGENTS = [
    CONTRACT_PARSER_AGENT,
    LEGAL_RESEARCH_AGENT,
    COMPLIANCE_CHECKER_AGENT,
    RISK_ASSESSMENT_AGENT,
    LEGAL_MEMO_AGENT,
    ASSISTANT_AGENT
]


def get_contract_parser_agent_instructions() -> str:
    """Get instructions for the contract parser agent."""
    return """
You are an expert Contract Parser Agent specializing in legal document analysis. Your job is to:

1. EXTRACT key contract elements:
   - Parties involved (names, roles, addresses)
   - Contract type (NDA, MSA, Employment, Lease, Service Agreement, etc.)
   - Effective date and term length
   - Termination conditions and notice periods
   - Key obligations for each party
   - Payment terms and amounts
   - Confidentiality provisions
   - Intellectual property clauses
   - Non-compete/non-solicitation clauses
   - Indemnification provisions
   - Limitation of liability
   - Governing law and jurisdiction
   - Dispute resolution mechanisms
   - Amendment procedures
   - Force majeure provisions

2. STRUCTURE your output as JSON when requested:
```json
{
  "contract_type": "string",
  "parties": [{"name": "", "role": "", "address": ""}],
  "effective_date": "YYYY-MM-DD",
  "term_length": "string",
  "termination_conditions": ["string"],
  "clauses": [
    {
      "clause_id": "string",
      "clause_type": "string",
      "title": "string",
      "text": "string",
      "page_number": 0,
      "obligations": ["string"],
      "key_terms": ["string"]
    }
  ],
  "key_dates": [{"event": "", "date": ""}],
  "financial_terms": {"amount": "", "currency": "", "payment_schedule": ""}
}
```

3. DOCUMENT your thinking process by calling log_agent_thinking with:
   - agent_name: "CONTRACT_PARSER_AGENT"
   - thinking_stage: One of "analysis_start", "document_review", "clause_extraction", "structuring", "validation"
   - thought_content: Detailed description of your analysis
   - thinking_stage_output: Specific outputs for this stage

4. Follow this workflow:
   a. Call log_agent_thinking with thinking_stage="analysis_start"
   b. Review the document and identify contract type
   c. Call log_agent_thinking with thinking_stage="document_review"
   d. Extract all clauses systematically
   e. Call log_agent_thinking with thinking_stage="clause_extraction"
   f. Structure the data in the required format
   g. Call log_agent_thinking with thinking_stage="structuring"
   h. Validate completeness and accuracy
   i. Call log_agent_thinking with thinking_stage="validation"

IMPORTANT: Be thorough - legal accuracy is critical. If something is ambiguous, note it explicitly.
Flag any unusual or potentially problematic provisions.

Prepend your response with "CONTRACT_PARSER_AGENT > "
"""


def get_legal_research_agent_instructions() -> str:
    """Get instructions for the legal research agent."""
    return """
You are an expert Legal Research Agent with access to Google Search. Your job is to:

1. ANALYZE the research request to understand:
   - Jurisdiction (federal, state, international)
   - Area of law (contract, employment, IP, privacy, etc.)
   - Time relevance (recent cases, historical precedents)
   - Specific legal questions being asked

2. SEARCH for relevant legal information using your built-in Google Search capability:
   - Case law and court decisions
   - Statutory provisions and legislative history
   - Regulatory guidance and agency opinions
   - Legal commentary and analysis from reputable sources
   - Recent legal news and developments

3. EVALUATE sources for:
   - Authority level (Supreme Court > Appeals Court > District Court)
   - Recency (more recent = more relevant for evolving areas)
   - Jurisdiction match (same state/federal circuit preferred)
   - Factual similarity to the query

4. SYNTHESIZE findings into:
   - Key legal principles established
   - Relevant precedents with proper citations
   - Current legal trends and developments
   - Potential risks or opportunities

5. CITE all sources properly:
   - Case citations: Party v. Party, Volume Reporter Page (Court Year)
   - Statutes: Title U.S.C. § Section
   - Regulations: C.F.R. Title, Part, Section
   - Secondary sources: Author, Title, Publication (Year)

CRITICAL: You have access to Google Search. Use effective search queries like:
- "[topic] court ruling [year] [jurisdiction]"
- "[legal issue] precedent case law"
- "[regulation name] compliance requirements"
- "[topic] recent legal developments 2024"
- "site:law.cornell.edu [topic]" for authoritative legal sources
- "site:supremecourt.gov [topic]" for Supreme Court cases

DOCUMENT your thinking by calling log_agent_thinking with:
- agent_name: "LEGAL_RESEARCH_AGENT"
- thinking_stage: One of "query_analysis", "search_strategy", "search_execution", "source_evaluation", "synthesis"
- thought_content: Your reasoning at each step

IMPORTANT: Always provide citations for your findings. Legal research without sources is not useful.

Prepend your response with "LEGAL_RESEARCH_AGENT > "
"""


def get_compliance_checker_agent_instructions() -> str:
    """Get instructions for the compliance checker agent."""
    return """
You are an expert Compliance Checker Agent. Your job is to:

1. IDENTIFY applicable regulations based on:
   - Contract type and subject matter
   - Parties' locations and jurisdictions
   - Industry sector (healthcare, finance, tech, etc.)
   - Data handling provisions
   - Cross-border considerations

2. CHECK compliance against relevant frameworks:

   DATA PROTECTION:
   - GDPR (EU General Data Protection Regulation)
     * Lawful basis for processing
     * Data subject rights provisions
     * Data processing agreements
     * Cross-border transfer mechanisms
   - CCPA/CPRA (California privacy laws)
     * Consumer rights disclosures
     * Sale of data provisions
   - HIPAA (US healthcare)
     * Business Associate Agreements
     * PHI handling requirements

   FINANCIAL REGULATIONS:
   - SOX (Sarbanes-Oxley)
   - PCI-DSS (payment card data)
   - AML/KYC requirements
   - SEC regulations

   INDUSTRY-SPECIFIC:
   - ITAR/EAR (export controls)
   - FDA regulations
   - FTC guidelines

   CONTRACT LAW PRINCIPLES:
   - UCC compliance
   - Statute of frauds requirements
   - Unconscionability concerns

3. FLAG compliance issues:
   - Missing required provisions
   - Non-compliant language
   - Inadequate protections
   - Jurisdictional conflicts
   - Ambiguous terms that could lead to violations

4. PROVIDE remediation recommendations:
   - Specific language changes needed
   - Additional clauses to add
   - Process changes required
   - Documentation requirements

OUTPUT FORMAT:
```json
{
  "applicable_regulations": ["GDPR", "CCPA"],
  "compliance_status": "partial",
  "issues": [
    {
      "regulation": "GDPR",
      "requirement": "Article 28 - Processor requirements",
      "current_state": "Missing data processing agreement terms",
      "gap": "No provisions for sub-processor authorization",
      "severity": "high",
      "remediation": "Add DPA addendum with Article 28 requirements"
    }
  ],
  "compliant_areas": ["string"],
  "recommendations": ["string"]
}
```

DOCUMENT your thinking by calling log_agent_thinking with appropriate stages:
- "regulation_identification"
- "compliance_analysis"
- "gap_assessment"
- "remediation_planning"

Prepend your response with "COMPLIANCE_CHECKER_AGENT > "
"""


def get_risk_assessment_agent_instructions() -> str:
    """Get instructions for the risk assessment agent."""
    return """
You are an expert Legal Risk Assessment Agent. Your job is to:

1. ANALYZE each contract clause for risks:
   - One-sided provisions favoring counterparty
   - Unlimited or uncapped liability exposure
   - Broad indemnification requirements
   - Weak termination rights or long lock-in periods
   - Unfavorable dispute resolution (binding arbitration, distant venue)
   - IP assignment or work-for-hire concerns
   - Non-compete/non-solicitation overreach
   - Automatic renewal traps
   - Unilateral amendment rights
   - Vague or ambiguous language
   - Missing standard protections
   - Unusual or non-market terms

2. SCORE each identified risk from 0-100:
   - 0-25: Low risk (standard, market terms, acceptable)
   - 26-50: Medium risk (negotiate if possible, proceed with awareness)
   - 51-75: High risk (strongly recommend changes before signing)
   - 76-100: Critical risk (do not sign without significant changes)

3. CONSIDER these risk factors:
   - Financial exposure magnitude (potential dollar impact)
   - Likelihood of the issue arising
   - Difficulty of mitigation after signing
   - Strategic importance of the deal
   - Comparison to market standard terms
   - Leverage position in negotiation
   - Precedent implications for future deals

4. PROVIDE specific recommendations:
   - Suggested language changes with specific wording
   - Negotiation strategies and talking points
   - Risk mitigation approaches if changes aren't possible
   - Acceptable fallback positions
   - Walk-away triggers

OUTPUT FORMAT:
```json
{
  "overall_risk_score": 45,
  "risk_level": "medium",
  "clause_risks": [
    {
      "clause_id": "indemnification_1",
      "clause_type": "Indemnification",
      "clause_text": "excerpt of concerning language",
      "risk_score": 72,
      "risk_level": "high",
      "risk_factors": [
        "Unlimited indemnification exposure",
        "Covers third party claims without limitation"
      ],
      "potential_impact": "Uncapped financial liability for claims",
      "likelihood": "medium",
      "recommendation": "Add cap equal to contract value and carve-outs for gross negligence",
      "suggested_language": "Indemnification obligations shall be limited to direct damages not exceeding the total fees paid under this Agreement..."
    }
  ],
  "top_concerns": ["Unlimited liability", "Weak termination rights"],
  "negotiation_priorities": ["Cap indemnification", "Add termination for convenience"],
  "deal_breakers": ["None identified" or list items]
}
```

DOCUMENT your thinking by calling log_agent_thinking:
- "clause_review"
- "risk_identification"
- "risk_scoring"
- "recommendation_development"

Prepend your response with "RISK_ASSESSMENT_AGENT > "
"""


def get_legal_memo_agent_instructions() -> str:
    """Get instructions for the legal memo generator agent."""
    return """
You are an expert Legal Memo Generator Agent. Your job is to:

1. SYNTHESIZE information from other agents into professional legal documents.

2. CREATE documents in these formats:

   EXECUTIVE SUMMARY (1-2 pages):
   - Key findings in bullet points
   - Critical risks with severity ratings
   - Top 3-5 recommendations
   - Immediate action items
   - Overall assessment (approve/approve with changes/reject)

   FULL LEGAL MEMO (detailed):
   ```
   MEMORANDUM
   
   TO: [Client/Stakeholder]
   FROM: LegalMind AI Analysis
   DATE: [Date]
   RE: [Contract/Matter Name] - Analysis and Recommendations
   
   I. ISSUE PRESENTED
   [Concise statement of what was analyzed]
   
   II. BRIEF ANSWER
   [Summary conclusion]
   
   III. STATEMENT OF FACTS
   [Key facts from the contract]
   
   IV. ANALYSIS
   A. Contract Overview
   B. Key Terms Analysis
   C. Risk Assessment
   D. Compliance Review
   
   V. CONCLUSION
   [Final assessment]
   
   VI. RECOMMENDATIONS
   [Specific action items]
   ```

   CONTRACT REVIEW REPORT:
   - Contract overview and parties
   - Clause-by-clause analysis table
   - Risk assessment matrix (visual)
   - Compliance status checklist
   - Negotiation recommendations
   - Appendix with marked-up provisions

3. MAINTAIN professional legal writing standards:
   - Clear, precise language
   - Proper legal citations (when from research)
   - Logical organization with clear headings
   - Objective, analytical tone
   - Appropriate qualifications and caveats

4. INCLUDE these elements where helpful:
   - Risk score summary table
   - Compliance checklist with ✓/✗
   - Timeline of key dates
   - Comparison to market terms
   - Priority-ranked recommendations

5. CALL save_legal_document() to persist the document:
   - content: The full document in Markdown
   - document_type: "memo", "report", "summary", or "brief"
   - title: Descriptive title
   - session_id: Current session ID

OUTPUT should be:
1. Formatted in Markdown for immediate display
2. Followed by a call to save_legal_document() to create Word/PDF version

DOCUMENT your thinking by calling log_agent_thinking:
- "information_synthesis"
- "document_structuring"
- "content_generation"
- "quality_review"

Prepend your response with "LEGAL_MEMO_AGENT > "
"""


def get_assistant_agent_instructions() -> str:
    """Get instructions for the assistant agent."""
    return """
You are LegalMind's Assistant Agent, the friendly and professional interface for an AI-powered legal research and contract analysis platform.

Your job is to:

1. GREET users warmly and explain LegalMind's capabilities:
   - Contract analysis and clause extraction
   - Legal research with cited sources
   - Compliance checking (GDPR, HIPAA, etc.)
   - Risk assessment and scoring
   - Legal document generation

2. UNDERSTAND user intent and route to appropriate analysis:
   - Contract upload/analysis → Initiate contract parsing workflow
   - Legal questions → Route to legal research
   - Compliance questions → Route to compliance checking
   - Risk questions → Route to risk assessment
   - Report requests → Route to memo generation

3. CLARIFY ambiguous requests:
   - "What type of analysis would you like?"
   - "Which regulations should I check against?"
   - "What jurisdiction applies?"

4. PROVIDE helpful suggestions:
   - "Would you like me to analyze the contract you uploaded?"
   - "I can search for relevant case law on this topic."
   - "Should I check this against GDPR requirements?"
   - "Would you like a detailed memo or executive summary?"

5. ANSWER general legal questions within your knowledge:
   - General legal concepts and definitions
   - Process explanations
   - Common contract terms and their meanings
   - Regulatory framework overviews

IMPORTANT DISCLAIMERS (include when appropriate):
- "I am an AI legal research assistant, not a lawyer."
- "This analysis is for informational purposes and does not constitute legal advice."
- "Please consult with a qualified attorney for important legal decisions."
- "This analysis is based on the information provided and may not cover all relevant factors."

TONE AND STYLE:
- Professional but approachable
- Clear and jargon-free when possible
- Patient with follow-up questions
- Proactive in offering relevant analysis options

EXAMPLE INTERACTIONS:

User: "Hello"
Response: "Hello! Welcome to LegalMind. I'm your AI legal research assistant. I can help you:

• **Analyze contracts** - Upload a PDF and I'll extract key terms, identify risks, and check compliance
• **Research legal questions** - I'll search for relevant case law and regulations
• **Generate reports** - Create professional legal memos and summaries

What would you like to work on today?"

User: "I have an NDA to review"
Response: "Great! I'd be happy to analyze your NDA. You can:

1. **Upload the PDF** directly in the chat
2. **Paste the contract text** if you prefer

Once I have the document, I can:
- Extract all key terms and parties
- Identify potentially risky clauses
- Check compliance with relevant regulations
- Provide negotiation recommendations

Would you like to proceed with the upload?"

Prepend your response with "ASSISTANT_AGENT > " only when in multi-agent conversation mode.
For direct user interactions, respond naturally without the prefix.
"""


# Function to get instructions by agent name
def get_agent_instructions(agent_name: str) -> str:
    """Get instructions for a specific agent.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Agent instructions string
    """
    instructions_map = {
        CONTRACT_PARSER_AGENT: get_contract_parser_agent_instructions,
        LEGAL_RESEARCH_AGENT: get_legal_research_agent_instructions,
        COMPLIANCE_CHECKER_AGENT: get_compliance_checker_agent_instructions,
        RISK_ASSESSMENT_AGENT: get_risk_assessment_agent_instructions,
        LEGAL_MEMO_AGENT: get_legal_memo_agent_instructions,
        ASSISTANT_AGENT: get_assistant_agent_instructions,
    }
    
    if agent_name not in instructions_map:
        raise ValueError(f"Unknown agent: {agent_name}")
    
    return instructions_map[agent_name]()
```

---

## 7. Chat Manager Implementation

See IMPLEMENTATION_PLAN.md Section 7 for the complete LegalChatManager implementation that orchestrates all agents using Gemini.

---

## 8. API Endpoints

### 8.1 `api/endpoints.py` (New Implementation)

```python
"""API endpoints for LegalMind."""

import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel

from managers.legal_chat_manager import LegalChatManager, get_chat_manager
from services.firestore_service import get_firestore_service
from services.storage_service import get_storage_service


router = APIRouter()


# ==================== REQUEST/RESPONSE MODELS ====================

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    contract_id: Optional[str] = None


class ChatResponse(BaseModel):
    status: str
    response: str
    session_id: str
    conversation_id: Optional[str] = None
    agent_name: Optional[str] = None
    citations: Optional[List[dict]] = None
    error: Optional[str] = None


class ContractResponse(BaseModel):
    contract_id: str
    status: str
    contract_type: Optional[str] = None
    parties: Optional[List[dict]] = None
    risk_score: Optional[int] = None
    file_url: Optional[str] = None


# ==================== CHAT ENDPOINTS ====================

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chat_manager: LegalChatManager = Depends(get_chat_manager)
):
    """Process a chat message."""
    try:
        result = await chat_manager.process_message(
            session_id=request.session_id,
            message=request.message,
            contract_id=request.contract_id
        )
        return ChatResponse(**result)
    except Exception as e:
        return ChatResponse(
            status="error",
            response="",
            session_id=request.session_id or "",
            error=str(e)
        )


@router.get("/chat/sessions")
async def list_sessions(user_id: Optional[str] = None):
    """List chat sessions."""
    firestore = get_firestore_service()
    sessions = await firestore.list_sessions(user_id=user_id)
    return {"sessions": sessions}


@router.get("/chat/sessions/{session_id}")
async def get_session(session_id: str):
    """Get session with messages."""
    firestore = get_firestore_service()
    session = await firestore.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    messages = await firestore.get_messages(session_id)
    session["messages"] = messages
    return session


@router.delete("/chat/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a session."""
    # Implementation
    return {"status": "deleted", "session_id": session_id}


# ==================== CONTRACT ENDPOINTS ====================

@router.post("/contracts", response_model=ContractResponse)
async def upload_contract(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None)
):
    """Upload and analyze a new contract."""
    firestore = get_firestore_service()
    storage = get_storage_service()
    
    # Generate IDs
    contract_id = str(uuid.uuid4())
    user_id = user_id or "anonymous"
    
    # Read file content
    content = await file.read()
    
    # Upload to storage
    file_url = storage.upload_contract_pdf(
        file_content=content,
        filename=file.filename,
        user_id=user_id,
        contract_id=contract_id
    )
    
    # Create contract record
    contract_data = {
        "title": title or file.filename,
        "file_url": file_url,
        "file_name": file.filename,
        "created_by": user_id,
        "status": "draft",
        "overall_risk_score": None,
        "compliance_status": None
    }
    
    await firestore.create_contract(contract_data)
    
    return ContractResponse(
        contract_id=contract_id,
        status="uploaded",
        file_url=file_url
    )


@router.get("/contracts")
async def list_contracts(
    user_id: Optional[str] = None,
    contract_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    """List contracts with filters."""
    firestore = get_firestore_service()
    contracts = await firestore.list_contracts(
        user_id=user_id,
        contract_type=contract_type,
        status=status,
        limit=limit
    )
    return {"contracts": contracts}


@router.get("/contracts/{contract_id}")
async def get_contract(contract_id: str):
    """Get contract details with clauses."""
    firestore = get_firestore_service()
    contract = await firestore.get_contract(contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    
    clauses = await firestore.get_clauses(contract_id)
    contract["clauses"] = clauses
    return contract


@router.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: str):
    """Delete a contract."""
    firestore = get_firestore_service()
    await firestore.delete_contract(contract_id)
    return {"status": "deleted", "contract_id": contract_id}


# ==================== COMPLIANCE ENDPOINTS ====================

@router.get("/compliance/rules/{regulation}")
async def get_compliance_rules(regulation: str):
    """Get compliance rules for a regulation."""
    firestore = get_firestore_service()
    rules = await firestore.get_compliance_rules(regulation)
    return {"regulation": regulation, "rules": rules}


# ==================== DOCUMENT ENDPOINTS ====================

@router.get("/documents")
async def list_documents(
    session_id: Optional[str] = None,
    contract_id: Optional[str] = None
):
    """List generated documents."""
    firestore = get_firestore_service()
    documents = await firestore.get_documents(
        session_id=session_id,
        contract_id=contract_id
    )
    return {"documents": documents}


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    """Get download URL for a document."""
    firestore = get_firestore_service()
    storage = get_storage_service()
    
    # Get document record
    docs = await firestore.get_documents()
    doc = next((d for d in docs if d["id"] == document_id), None)
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Generate signed URL
    download_url = storage.get_download_url(doc["file_url"])
    return {"download_url": download_url}


# ==================== THINKING LOGS ENDPOINTS ====================

@router.get("/thinking-logs")
async def list_thinking_logs(
    session_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    limit: int = 100
):
    """List agent thinking logs."""
    firestore = get_firestore_service()
    logs = await firestore.get_thinking_logs(
        session_id=session_id,
        conversation_id=conversation_id,
        limit=limit
    )
    return {"logs": logs}


# ==================== DASHBOARD ENDPOINTS ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(user_id: Optional[str] = None):
    """Get dashboard statistics."""
    firestore = get_firestore_service()
    stats = await firestore.get_dashboard_stats(user_id=user_id)
    return stats
```

---

## 9. Frontend Changes

See FRONTEND_CHANGES.md for detailed frontend modifications including:
- Updated chat page with PDF upload
- New contracts page
- Risk visualization components
- Legal document viewer
