"""
Clause Tools
Tools for clause extraction and analysis.
"""

from typing import Dict, List, Any, Optional

from services.firestore_service import get_firestore_service


async def extract_clauses(
    contract_id: str,
    content: str,
) -> Dict[str, Any]:
    """Extract and categorize clauses from contract text.
    
    Args:
        contract_id: The contract ID
        content: Contract text content
        
    Returns:
        Extracted clauses with categories
    """
    firestore = get_firestore_service()
    
    # Common clause patterns to identify
    clause_patterns = {
        "indemnification": ["indemnif", "hold harmless", "defend and indemnify"],
        "limitation_of_liability": ["limitation of liability", "limited liability", "cap on damages"],
        "confidentiality": ["confidential", "non-disclosure", "proprietary information"],
        "termination": ["terminat", "cancellation", "end of agreement"],
        "intellectual_property": ["intellectual property", "ip rights", "patent", "copyright", "trademark"],
        "payment": ["payment terms", "compensation", "fees", "invoic"],
        "warranties": ["warrant", "representation", "guarantee"],
        "governing_law": ["governing law", "jurisdiction", "venue", "applicable law"],
        "dispute_resolution": ["arbitrat", "mediat", "dispute resolution"],
        "force_majeure": ["force majeure", "act of god", "unforeseen circumstances"],
        "assignment": ["assign", "transfer of rights", "novation"],
        "non_compete": ["non-compete", "non-competition", "restrictive covenant"],
        "data_protection": ["data protection", "privacy", "gdpr", "personal data"],
    }
    
    # Simple clause extraction (in production, use NLP/ML)
    lines = content.split('\n')
    extracted_clauses = []
    current_section = ""
    current_content = []
    section_number = 0
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Check if this is a section header
        is_header = (
            line.isupper() or
            line.endswith(':') or
            (len(line) < 100 and any(char.isdigit() for char in line[:5]))
        )
        
        if is_header and current_section and current_content:
            # Save previous section
            section_text = ' '.join(current_content)
            clause_type = _identify_clause_type(section_text, clause_patterns)
            
            extracted_clauses.append({
                "section_number": str(section_number),
                "clause_type": clause_type,
                "title": current_section,
                "content": section_text[:1000],  # Truncate for storage
            })
            current_content = []
            section_number += 1
        
        if is_header:
            current_section = line
        else:
            current_content.append(line)
    
    # Don't forget the last section
    if current_section and current_content:
        section_text = ' '.join(current_content)
        clause_type = _identify_clause_type(section_text, clause_patterns)
        extracted_clauses.append({
            "section_number": str(section_number),
            "clause_type": clause_type,
            "title": current_section,
            "content": section_text[:1000],
        })
    
    # Save clauses to Firestore
    clause_ids = []
    for clause in extracted_clauses:
        clause_id = await firestore.create_clause(
            contract_id=contract_id,
            clause_type=clause["clause_type"],
            content=clause["content"],
            section_number=clause["section_number"],
        )
        clause_ids.append(clause_id)
        clause["id"] = clause_id
    
    # Update contract with clause IDs
    await firestore.update_document(
        firestore.CONTRACTS,
        contract_id,
        {"clauses": clause_ids}
    )
    
    return {
        "status": "success",
        "clauses": extracted_clauses,
        "count": len(extracted_clauses)
    }


def _identify_clause_type(text: str, patterns: Dict[str, List[str]]) -> str:
    """Identify clause type based on content patterns."""
    text_lower = text.lower()
    
    for clause_type, keywords in patterns.items():
        for keyword in keywords:
            if keyword in text_lower:
                return clause_type
    
    return "general"


async def get_clause(clause_id: str) -> Dict[str, Any]:
    """Get a specific clause by ID.
    
    Args:
        clause_id: The clause ID
        
    Returns:
        Clause data
    """
    firestore = get_firestore_service()
    clause = await firestore.get_document(firestore.CLAUSES, clause_id)
    
    if clause:
        return {
            "status": "success",
            "clause": clause
        }
    return {
        "status": "error",
        "message": f"Clause {clause_id} not found"
    }


async def get_contract_clauses(
    contract_id: str,
    clause_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Get all clauses for a contract.
    
    Args:
        contract_id: The contract ID
        clause_type: Optional filter by clause type
        
    Returns:
        List of clauses
    """
    firestore = get_firestore_service()
    clauses = await firestore.get_clauses_for_contract(contract_id)
    
    if clause_type:
        clauses = [c for c in clauses if c.get("clause_type") == clause_type]
    
    return {
        "status": "success",
        "clauses": clauses,
        "count": len(clauses)
    }


async def update_clause_analysis(
    clause_id: str,
    risk_level: Optional[str] = None,
    risk_explanation: Optional[str] = None,
    compliance_issues: Optional[List[str]] = None,
    recommendations: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Update clause with analysis results.
    
    Args:
        clause_id: The clause ID
        risk_level: Risk level (low, medium, high, critical)
        risk_explanation: Explanation of the risk
        compliance_issues: List of compliance concerns
        recommendations: Suggested changes
        
    Returns:
        Update status
    """
    firestore = get_firestore_service()
    
    update_data = {}
    if risk_level:
        update_data["risk_level"] = risk_level
    if risk_explanation:
        update_data["risk_explanation"] = risk_explanation
    if compliance_issues:
        update_data["compliance_issues"] = compliance_issues
    if recommendations:
        update_data["recommendations"] = recommendations
    
    if update_data:
        await firestore.update_document(firestore.CLAUSES, clause_id, update_data)
        return {
            "status": "success",
            "message": "Clause analysis updated"
        }
    
    return {
        "status": "error",
        "message": "No analysis data provided"
    }


async def find_similar_clauses(
    clause_type: str,
    risk_level: Optional[str] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Find similar clauses across contracts.
    
    Args:
        clause_type: Type of clause to find
        risk_level: Optional filter by risk level
        limit: Maximum results
        
    Returns:
        List of similar clauses
    """
    firestore = get_firestore_service()
    
    filters = [("clause_type", "==", clause_type)]
    if risk_level:
        filters.append(("risk_level", "==", risk_level))
    
    clauses = await firestore.query_documents(
        firestore.CLAUSES,
        filters=filters,
        limit=limit
    )
    
    return {
        "status": "success",
        "clauses": clauses,
        "count": len(clauses)
    }


# Tool definitions for Gemini function calling
CLAUSE_TOOLS = [
    {
        "name": "extract_clauses",
        "description": "Extract and categorize all clauses from contract text. Identifies clause types like indemnification, confidentiality, termination, etc.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The contract ID"
                },
                "content": {
                    "type": "string",
                    "description": "The full contract text content to extract clauses from"
                }
            },
            "required": ["contract_id", "content"]
        },
        "handler": extract_clauses
    },
    {
        "name": "get_clause",
        "description": "Get detailed information about a specific clause by ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "clause_id": {
                    "type": "string",
                    "description": "The clause ID"
                }
            },
            "required": ["clause_id"]
        },
        "handler": get_clause
    },
    {
        "name": "get_contract_clauses",
        "description": "Get all clauses for a contract, optionally filtered by type.",
        "parameters": {
            "type": "object",
            "properties": {
                "contract_id": {
                    "type": "string",
                    "description": "The contract ID"
                },
                "clause_type": {
                    "type": "string",
                    "description": "Filter by clause type",
                    "enum": [
                        "indemnification",
                        "limitation_of_liability",
                        "confidentiality",
                        "termination",
                        "intellectual_property",
                        "payment",
                        "warranties",
                        "governing_law",
                        "dispute_resolution",
                        "force_majeure",
                        "assignment",
                        "non_compete",
                        "data_protection",
                        "general"
                    ]
                }
            },
            "required": ["contract_id"]
        },
        "handler": get_contract_clauses
    },
    {
        "name": "update_clause_analysis",
        "description": "Save analysis results for a clause including risk level, compliance issues, and recommendations.",
        "parameters": {
            "type": "object",
            "properties": {
                "clause_id": {
                    "type": "string",
                    "description": "The clause ID to update"
                },
                "risk_level": {
                    "type": "string",
                    "description": "Risk assessment level",
                    "enum": ["low", "medium", "high", "critical"]
                },
                "risk_explanation": {
                    "type": "string",
                    "description": "Detailed explanation of the identified risk"
                },
                "compliance_issues": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of compliance concerns"
                },
                "recommendations": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Suggested changes or improvements"
                }
            },
            "required": ["clause_id"]
        },
        "handler": update_clause_analysis
    },
    {
        "name": "find_similar_clauses",
        "description": "Find similar clauses across all contracts for comparison or benchmarking.",
        "parameters": {
            "type": "object",
            "properties": {
                "clause_type": {
                    "type": "string",
                    "description": "Type of clause to search for"
                },
                "risk_level": {
                    "type": "string",
                    "description": "Filter by risk level",
                    "enum": ["low", "medium", "high", "critical"]
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum results (default 10)"
                }
            },
            "required": ["clause_type"]
        },
        "handler": find_similar_clauses
    }
]


def get_clause_tools() -> List[Dict[str, Any]]:
    """Get all clause tool definitions."""
    return CLAUSE_TOOLS


# Export for tool registry
TOOL_DEFINITIONS = CLAUSE_TOOLS
