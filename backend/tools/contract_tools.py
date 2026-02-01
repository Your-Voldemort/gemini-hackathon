"""
Contract Tools
Tools for contract parsing and management.
"""

from typing import Dict, List, Any, Optional
import PyPDF2
import pdfplumber
import io

from services.firestore_service import get_firestore_service
from services.storage_service import get_storage_service


async def get_contract(contract_id: str) -> Dict[str, Any]:
    """Retrieve a contract by ID.
    
    Args:
        contract_id: The contract ID
        
    Returns:
        Contract data or error message
    """
    firestore = get_firestore_service()
    contract = await firestore.get_contract(contract_id)
    
    if contract:
        return {
            "status": "success",
            "contract": contract
        }
    else:
        return {
            "status": "error",
            "message": f"Contract {contract_id} not found"
        }


async def list_contracts(
    status: Optional[str] = None,
    contract_type: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """List contracts with optional filters.
    
    Args:
        status: Filter by status (pending_analysis, analyzed)
        contract_type: Filter by contract type (NDA, MSA, etc.)
        limit: Maximum number of results
        
    Returns:
        List of contracts
    """
    firestore = get_firestore_service()
    contracts = await firestore.list_contracts(
        status=status,
        contract_type=contract_type,
        limit=limit
    )
    
    return {
        "status": "success",
        "contracts": contracts,
        "count": len(contracts)
    }


async def extract_contract_text(contract_id: str) -> Dict[str, Any]:
    """Extract text content from a contract PDF.
    
    Args:
        contract_id: The contract ID
        
    Returns:
        Extracted text content
    """
    try:
        firestore = get_firestore_service()
        storage = get_storage_service()
        
        # Get contract metadata
        contract = await firestore.get_contract(contract_id)
        if not contract:
            return {
                "status": "error",
                "message": f"Contract {contract_id} not found"
            }
        
        # Check if content already extracted
        if contract.get("content"):
            return {
                "status": "success",
                "content": contract["content"],
                "source": "cached"
            }
        
        # Download and extract
        file_url = contract.get("file_url")
        if not file_url:
            return {
                "status": "error",
                "message": "No file associated with contract"
            }
        
        pdf_bytes = await storage.download_file(file_url)
        
        # Extract text using pdfplumber (better quality)
        text_content = ""
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content += page_text + "\n\n"
        
        # Update contract with extracted content
        await firestore.update_document(
            firestore.CONTRACTS,
            contract_id,
            {"content": text_content}
        )
        
        return {
            "status": "success",
            "content": text_content,
            "source": "extracted",
            "page_count": len(pdf.pages) if pdf else 0
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to extract text: {str(e)}"
        }


async def update_contract_metadata(
    contract_id: str,
    contract_type: Optional[str] = None,
    parties: Optional[List[Dict]] = None,
    key_dates: Optional[List[Dict]] = None,
    status: Optional[str] = None,
) -> Dict[str, Any]:
    """Update contract metadata.
    
    Args:
        contract_id: The contract ID
        contract_type: Type of contract
        parties: List of parties with name and role
        key_dates: List of important dates
        status: Contract status
        
    Returns:
        Update status
    """
    firestore = get_firestore_service()
    
    update_data = {}
    if contract_type:
        update_data["contract_type"] = contract_type
    if parties:
        update_data["parties"] = parties
    if key_dates:
        update_data["key_dates"] = key_dates
    if status:
        update_data["status"] = status
    
    if update_data:
        await firestore.update_document(
            firestore.CONTRACTS,
            contract_id,
            update_data
        )
        return {
            "status": "success",
            "message": "Contract updated successfully",
            "updated_fields": list(update_data.keys())
        }
    
    return {
        "status": "error",
        "message": "No fields to update"
    }


async def search_contracts(
    query: str,
    limit: int = 20
) -> Dict[str, Any]:
    """Search contracts by text content.
    
    Note: For full-text search, you might want to use
    a dedicated search service or Firestore's array-contains.
    This is a simplified implementation.
    
    Args:
        query: Search query
        limit: Maximum results
        
    Returns:
        Matching contracts
    """
    firestore = get_firestore_service()
    
    # Get all contracts and filter (simple implementation)
    # For production, consider using Firestore's full-text search
    # or integrating with Algolia/Elasticsearch
    all_contracts = await firestore.list_contracts(limit=100)
    
    query_lower = query.lower()
    matching = []
    
    for contract in all_contracts:
        title = contract.get("title", "").lower()
        content = contract.get("content", "").lower()
        
        if query_lower in title or query_lower in content:
            # Add relevance score (simple)
            score = 0
            if query_lower in title:
                score += 10
            if query_lower in content:
                score += content.count(query_lower)
            
            contract["_relevance_score"] = score
            matching.append(contract)
    
    # Sort by relevance
    matching.sort(key=lambda x: x.get("_relevance_score", 0), reverse=True)
    
    return {
        "status": "success",
        "contracts": matching[:limit],
        "count": len(matching[:limit]),
        "total_matches": len(matching)
    }


# Tool definitions for Gemini function calling
CONTRACT_TOOLS = [
    {
        "name": "get_contract",
        "description": "Retrieve a contract by its ID. Returns full contract details including metadata, parties, and analysis status.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The unique identifier of the contract"
                }
            },
            "required": ["contract_id"]
        },
        "handler": get_contract
    },
    {
        "name": "list_contracts",
        "description": "List all contracts with optional filters. Can filter by status (pending_analysis, analyzed) or contract type (NDA, MSA, Employment, Lease).",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Filter by analysis status",
                    "enum": ["pending_analysis", "analyzed"]
                },
                "contract_type": {
                    "type": "string",
                    "description": "Filter by contract type"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default 50)"
                }
            }
        },
        "handler": list_contracts
    },
    {
        "name": "extract_contract_text",
        "description": "Extract and return the full text content from a contract PDF. Use this to read the actual contract text for analysis.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The contract ID to extract text from"
                }
            },
            "required": ["contract_id"]
        },
        "handler": extract_contract_text
    },
    {
        "name": "update_contract_metadata",
        "description": "Update contract metadata after analysis. Use this to save identified contract type, parties, and key dates.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The contract ID to update"
                },
                "contract_type": {
                    "type": "string",
                    "description": "Type of contract (NDA, MSA, Employment, Lease, etc.)"
                },
                "parties": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "role": {"type": "string"}
                        }
                    },
                    "description": "List of parties involved with their roles"
                },
                "key_dates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    },
                    "description": "Important dates in the contract"
                },
                "status": {
                    "type": "string",
                    "description": "Contract status",
                    "enum": ["pending_analysis", "analyzed", "active", "expired"]
                }
            },
            "required": ["contract_id"]
        },
        "handler": update_contract_metadata
    },
    {
        "name": "search_contracts",
        "description": "Search contracts by text content or title. Returns matching contracts sorted by relevance.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query text"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results (default 20)"
                }
            },
            "required": ["query"]
        },
        "handler": search_contracts
    }
]


def get_contract_tools() -> List[Dict[str, Any]]:
    """Get all contract tool definitions."""
    return CONTRACT_TOOLS


# Export for tool registry
TOOL_DEFINITIONS = CONTRACT_TOOLS
