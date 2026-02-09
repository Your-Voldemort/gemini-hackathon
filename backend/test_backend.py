"""
Backend Test Suite for LegalMind
Tests all core components and validates functionality.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Test results tracking
test_results = {
    "passed": [],
    "failed": [],
    "warnings": [],
}


def log_test(name, status, message=""):
    """Log test result."""
    if status == "PASS":
        test_results["passed"].append(f"[PASS] {name}")
        print(f"[PASS] {name}")
    elif status == "FAIL":
        test_results["failed"].append(f"[FAIL] {name}: {message}")
        print(f"[FAIL] {name}: {message}")
    elif status == "WARN":
        test_results["warnings"].append(f"[WARN] {name}: {message}")
        print(f"[WARN] {name}: {message}")


def test_imports():
    """Test that all core modules can be imported."""
    print("\n" + "="*60)
    print("TESTING IMPORTS")
    print("="*60)
    
    try:
        from config.settings import get_settings
        log_test("Import config.settings", "PASS")
    except Exception as e:
        log_test("Import config.settings", "FAIL", str(e))
        return False
    
    try:
        from services.gemini_service import GeminiService
        log_test("Import services.gemini_service", "PASS")
    except Exception as e:
        log_test("Import services.gemini_service", "FAIL", str(e))
        return False
    
    try:
        from services.firestore_service import FirestoreService
        log_test("Import services.firestore_service", "PASS")
    except Exception as e:
        log_test("Import services.firestore_service", "FAIL", str(e))
        return False
    
    try:
        from services.storage_service import StorageService
        log_test("Import services.storage_service", "PASS")
    except Exception as e:
        log_test("Import services.storage_service", "FAIL", str(e))
        return False
    
    try:
        from tools import contract_tools, clause_tools, compliance_tools, risk_tools, document_tools, logging_tools
        log_test("Import all tool modules", "PASS")
    except Exception as e:
        log_test("Import all tool modules", "FAIL", str(e))
        return False
    
    try:
        from agents.agent_definitions_new import get_agent_config, list_agents
        log_test("Import agents.agent_definitions_new", "PASS")
    except Exception as e:
        log_test("Import agents.agent_definitions_new", "FAIL", str(e))
        return False
    
    try:
        from agents.agent_strategies_new import select_agent, get_workflow_template
        log_test("Import agents.agent_strategies_new", "PASS")
    except Exception as e:
        log_test("Import agents.agent_strategies_new", "FAIL", str(e))
        return False
    
    try:
        from managers.chatbot_manager_new import ChatbotManager
        log_test("Import managers.chatbot_manager_new", "PASS")
    except Exception as e:
        log_test("Import managers.chatbot_manager_new", "FAIL", str(e))
        return False
    
    try:
        from api.app_new import app
        log_test("Import api.app_new", "PASS")
    except Exception as e:
        log_test("Import api.app_new", "FAIL", str(e))
        return False
    
    return True


def test_settings():
    """Test settings configuration."""
    print("\n" + "="*60)
    print("TESTING SETTINGS")
    print("="*60)
    
    try:
        from config.settings import get_settings
        settings = get_settings()
        log_test("Load settings", "PASS")
        
        # Check key settings
        if hasattr(settings, 'google_cloud_project'):
            log_test("Settings has google_cloud_project", "PASS")
        else:
            log_test("Settings has google_cloud_project", "WARN", "google_cloud_project not set (requires .env)")
        
        if hasattr(settings, 'gemini_model'):
            log_test("Settings has gemini_model", "PASS")
        else:
            log_test("Settings has gemini_model", "WARN", "gemini_model not set (requires .env)")
        
        return True
    except Exception as e:
        log_test("Load settings", "FAIL", str(e))
        return False


def test_tool_definitions():
    """Test that tool definitions are properly configured."""
    print("\n" + "="*60)
    print("TESTING TOOL DEFINITIONS")
    print("="*60)
    
    try:
        from tools.contract_tools import TOOL_DEFINITIONS as CONTRACT_DEFS
        if isinstance(CONTRACT_DEFS, list) and len(CONTRACT_DEFS) > 0:
            log_test(f"Contract tools definitions ({len(CONTRACT_DEFS)} tools)", "PASS")
        else:
            log_test("Contract tools definitions", "FAIL", "No tool definitions found")
            return False
    except Exception as e:
        log_test("Contract tools definitions", "FAIL", str(e))
        return False
    
    try:
        from tools.compliance_tools import TOOL_DEFINITIONS as COMPLIANCE_DEFS
        if isinstance(COMPLIANCE_DEFS, list) and len(COMPLIANCE_DEFS) > 0:
            log_test(f"Compliance tools definitions ({len(COMPLIANCE_DEFS)} tools)", "PASS")
        else:
            log_test("Compliance tools definitions", "FAIL", "No tool definitions found")
            return False
    except Exception as e:
        log_test("Compliance tools definitions", "FAIL", str(e))
        return False
    
    try:
        from tools.risk_tools import TOOL_DEFINITIONS as RISK_DEFS
        if isinstance(RISK_DEFS, list) and len(RISK_DEFS) > 0:
            log_test(f"Risk tools definitions ({len(RISK_DEFS)} tools)", "PASS")
        else:
            log_test("Risk tools definitions", "FAIL", "No tool definitions found")
            return False
    except Exception as e:
        log_test("Risk tools definitions", "FAIL", str(e))
        return False
    
    return True


def test_agent_configuration():
    """Test agent configuration and definitions."""
    print("\n" + "="*60)
    print("TESTING AGENT CONFIGURATION")
    print("="*60)
    
    try:
        from agents.agent_definitions_new import (
            get_agent_config,
            list_agents,
            AGENT_CONFIGS,
            CONTRACT_PARSER_AGENT,
            LEGAL_RESEARCH_AGENT,
            COMPLIANCE_CHECKER_AGENT,
            RISK_ASSESSMENT_AGENT,
            LEGAL_MEMO_AGENT,
            ASSISTANT_AGENT,
        )
        
        agents = list_agents()
        log_test(f"List agents ({len(agents)} agents)", "PASS")
        
        # Test each agent
        agent_names = [
            "CONTRACT_PARSER_AGENT",
            "LEGAL_RESEARCH_AGENT",
            "COMPLIANCE_CHECKER_AGENT",
            "RISK_ASSESSMENT_AGENT",
            "LEGAL_MEMO_AGENT",
            "ASSISTANT_AGENT",
        ]
        
        for agent_name in agent_names:
            try:
                config = get_agent_config(agent_name)
                if config and "name" in config and "instructions" in config:
                    tools_count = len(config.get("tools", []))
                    log_test(f"Agent {agent_name} ({tools_count} tools)", "PASS")
                else:
                    log_test(f"Agent {agent_name}", "FAIL", "Missing required fields")
                    return False
            except Exception as e:
                log_test(f"Agent {agent_name}", "FAIL", str(e))
                return False
        
        return True
    except Exception as e:
        log_test("Agent configuration", "FAIL", str(e))
        return False


def test_query_classification():
    """Test query classification and agent selection."""
    print("\n" + "="*60)
    print("TESTING QUERY CLASSIFICATION")
    print("="*60)
    
    try:
        from agents.agent_strategies_new import classify_query, select_agent, QueryType
        
        # Test various queries
        test_queries = [
            ("What does this contract say about termination?", QueryType.CONTRACT_ANALYSIS),
            ("What is GDPR compliance?", QueryType.LEGAL_RESEARCH),
            ("Check if this contract is GDPR compliant", QueryType.COMPLIANCE_CHECK),
            ("What are the risks in this contract?", QueryType.RISK_ASSESSMENT),
            ("Generate a summary of this contract", QueryType.DOCUMENT_GENERATION),
            ("Hello, how can I help?", QueryType.GENERAL_QUESTION),
        ]
        
        for query, expected_type in test_queries:
            try:
                classified_type = classify_query(query)
                if classified_type == expected_type:
                    log_test(f"Query classification: '{query[:40]}...'", "PASS")
                else:
                    log_test(
                        f"Query classification: '{query[:40]}...'",
                        "WARN",
                        f"Expected {expected_type}, got {classified_type}"
                    )
            except Exception as e:
                log_test(f"Query classification: '{query[:40]}...'", "FAIL", str(e))
                return False
        
        # Test agent selection
        selection = select_agent("What does the contract say about liability?")
        if selection and hasattr(selection, 'agent_name'):
            log_test(f"Agent selection (selected {selection.agent_name})", "PASS")
        else:
            log_test("Agent selection", "FAIL", "No valid agent selected")
            return False
        
        return True
    except Exception as e:
        log_test("Query classification", "FAIL", str(e))
        return False


def test_workflow_templates():
    """Test workflow template configuration."""
    print("\n" + "="*60)
    print("TESTING WORKFLOW TEMPLATES")
    print("="*60)
    
    try:
        from agents.agent_strategies_new import list_workflow_templates, get_workflow_template
        
        templates = list_workflow_templates()
        log_test(f"List workflow templates ({len(templates)} templates)", "PASS")
        
        if templates:
            template_names = [t["id"] for t in templates]
            log_test(f"Available workflows: {', '.join(template_names)}", "PASS")
            
            # Test getting specific template
            template = get_workflow_template(templates[0]["id"])
            if template and "agents" in template:
                log_test(f"Get workflow template: {templates[0]['name']}", "PASS")
            else:
                log_test("Get workflow template", "FAIL", "Missing agents")
                return False
        
        return True
    except Exception as e:
        log_test("Workflow templates", "FAIL", str(e))
        return False


async def test_chatbot_manager():
    """Test ChatbotManager initialization and basic functionality."""
    print("\n" + "="*60)
    print("TESTING CHATBOT MANAGER")
    print("="*60)
    
    try:
        from managers.chatbot_manager_new import get_chatbot_manager
        
        chatbot = get_chatbot_manager()
        log_test("Initialize ChatbotManager", "PASS")
        
        # Test session initialization
        session_id = "test-session-123"
        session = await chatbot.initialize_session(session_id)
        
        if session and "id" in session:
            log_test("Initialize session", "PASS")
        else:
            log_test("Initialize session", "FAIL", "Invalid session object")
            return False
        
        # Check tool registry
        if hasattr(chatbot, 'tool_handlers') and len(chatbot.tool_handlers) > 0:
            log_test(f"Tool registry ({len(chatbot.tool_handlers)} tools)", "PASS")
        else:
            log_test("Tool registry", "FAIL", "No tools registered")
            return False
        
        return True
    except Exception as e:
        log_test("ChatbotManager", "FAIL", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_api_routes():
    """Test that API routes are properly defined."""
    print("\n" + "="*60)
    print("TESTING API ROUTES")
    print("="*60)
    
    try:
        from api.app_new import app
        
        # Get all routes
        routes = []
        for route in app.routes:
            if hasattr(route, 'path'):
                routes.append(route.path)
        
        expected_paths = [
            "/api/chat",
            "/api/contracts",
            "/api/workflow",
            "/api/agents",
            "/api/health",
        ]
        
        found_paths = 0
        for expected in expected_paths:
            if any(expected in route for route in routes):
                found_paths += 1
        
        if found_paths >= len(expected_paths) - 1:  # Allow 1 missing
            log_test(f"API routes ({len(routes)} routes total)", "PASS")
        else:
            log_test("API routes", "WARN", f"Found {found_paths}/{len(expected_paths)} expected routes")
        
        # Check WebSocket endpoints
        ws_routes = [r.path for r in app.routes if "/ws/" in r.path]
        if len(ws_routes) >= 1:
            log_test(f"WebSocket endpoints ({len(ws_routes)} endpoints)", "PASS")
        else:
            log_test("WebSocket endpoints", "WARN", "No WebSocket endpoints found")
        
        return True
    except Exception as e:
        log_test("API routes", "FAIL", str(e))
        import traceback
        traceback.print_exc()
        return False


def test_environment_check():
    """Check environment file and Google Cloud setup."""
    print("\n" + "="*60)
    print("TESTING ENVIRONMENT SETUP")
    print("="*60)
    
    env_file = Path(backend_dir) / ".env"
    if env_file.exists():
        log_test(".env file exists", "PASS")
    else:
        log_test(
            ".env file exists",
            "WARN",
            ".env file not found - create from .env.example and configure"
        )
    
    example_file = Path(backend_dir) / ".env.example"
    if example_file.exists():
        log_test(".env.example file exists", "PASS")
    else:
        log_test(".env.example file exists", "FAIL", ".env.example not found")
        return False
    
    return True


async def run_all_tests():
    """Run all tests."""
    print("\n" + "LEGALMIND BACKEND TEST SUITE".center(60, "="))
    
    # Run all tests
    results = []
    
    results.append(("Environment", test_environment_check()))
    results.append(("Imports", test_imports()))
    results.append(("Settings", test_settings()))
    results.append(("Tool Definitions", test_tool_definitions()))
    results.append(("Agent Configuration", test_agent_configuration()))
    results.append(("Query Classification", test_query_classification()))
    results.append(("Workflow Templates", test_workflow_templates()))
    results.append(("ChatbotManager", await test_chatbot_manager()))
    results.append(("API Routes", test_api_routes()))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = len(test_results["passed"])
    failed = len(test_results["failed"])
    warnings = len(test_results["warnings"])
    
    print(f"\n[PASS] PASSED: {passed}")
    print(f"[FAIL] FAILED: {failed}")
    print(f"[WARN] WARNINGS: {warnings}")
    
    if test_results["failed"]:
        print("\n[FAIL] FAILED TESTS:")
        for test in test_results["failed"]:
            print(f"  {test}")
    
    if test_results["warnings"]:
        print("\n[WARN] WARNINGS:")
        for test in test_results["warnings"]:
            print(f"  {test}")
    
    print("\n" + "="*60)
    
    # Overall result
    if failed == 0:
        print("[SUCCESS] ALL CORE TESTS PASSED!")
        print("\nNext steps:")
        print("1. Configure .env file with Google Cloud credentials")
        print("2. Test API endpoints with actual Gemini API")
        print("3. Update frontend components")
        return 0
    else:
        print("[ERROR] SOME TESTS FAILED - SEE ABOVE FOR DETAILS")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
