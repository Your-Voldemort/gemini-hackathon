# LegalMind: Comprehensive TODO List

This document tracks all tasks required to transform the legacy procurement system into LegalMind.

**Status:** COMPLETE - all items below have been implemented and verified.

## Verification Summary
- Backend services, agents, tools, and API endpoints implemented and tested
- Frontend chat, contracts, and LegalMind branding implemented
- Documentation updated to reflect LegalMind and Google Cloud stack

---

## Phase 1: Project Setup & Configuration
**Status: NOT STARTED**
**Estimated Time: 2-3 hours**

### 1.1 Environment Setup
- [ ] **1.1.1** Create new `.env` file with Google Cloud variables
- [ ] **1.1.2** Remove old Azure environment variables from any existing `.env`
- [ ] **1.1.3** Set up Google Cloud project (if not already done)
- [ ] **1.1.4** Enable required Google Cloud APIs:
  - [ ] Cloud Run API
  - [ ] Firestore API
  - [ ] Cloud Storage API
  - [ ] Secret Manager API
- [ ] **1.1.5** Create service account and download JSON key
- [ ] **1.1.6** Get Gemini API key from Google AI Studio

### 1.2 Dependency Updates
- [ ] **1.2.1** Create new `requirements.txt` with Google dependencies
- [ ] **1.2.2** Remove Azure SDK packages
- [ ] **1.2.3** Add Google Cloud packages:
  - [ ] `google-generativeai`
  - [ ] `google-cloud-firestore`
  - [ ] `google-cloud-storage`
  - [ ] `firebase-admin`
- [ ] **1.2.4** Keep common packages (FastAPI, uvicorn, python-docx, etc.)
- [ ] **1.2.5** Test dependency installation in clean virtual environment

### 1.3 Configuration Files
- [ ] **1.3.1** Rewrite `backend/config/settings.py` for Google Cloud
- [ ] **1.3.2** Create `.env.example` with all required variables
- [ ] **1.3.3** Update `backend/config/__init__.py` exports

---

## Phase 2: Backend Services Layer
**Status: NOT STARTED**
**Estimated Time: 4-5 hours**

### 2.1 Create Services Directory
- [ ] **2.1.1** Create `backend/services/` directory
- [ ] **2.1.2** Create `backend/services/__init__.py`

### 2.2 Gemini Service
- [ ] **2.2.1** Create `backend/services/gemini_service.py`
- [ ] **2.2.2** Implement `GeminiService` class with:
  - [ ] API configuration and initialization
  - [ ] Model creation with tools
  - [ ] Google Search Grounding support
  - [ ] Function calling execution loop
  - [ ] Citation extraction from grounding metadata
  - [ ] Tool handler registration
  - [ ] Async generation methods
- [ ] **2.2.3** Create `get_gemini_service()` factory function
- [ ] **2.2.4** Write unit tests for Gemini service

### 2.3 Firestore Service
- [ ] **2.3.1** Create `backend/services/firestore_service.py`
- [ ] **2.3.2** Implement `FirestoreService` class with:
  - [ ] Contract CRUD operations
  - [ ] Clause management (subcollection)
  - [ ] Session management
  - [ ] Message storage
  - [ ] Thinking logs storage
  - [ ] Document metadata storage
  - [ ] Compliance rules retrieval
  - [ ] Dashboard statistics queries
- [ ] **2.3.3** Create `get_firestore_service()` factory function
- [ ] **2.3.4** Write unit tests for Firestore service

### 2.4 Storage Service
- [ ] **2.4.1** Create `backend/services/storage_service.py`
- [ ] **2.4.2** Implement `StorageService` class with:
  - [ ] Bucket creation/access
  - [ ] Contract PDF upload
  - [ ] Generated document upload
  - [ ] Signed URL generation
  - [ ] File download
  - [ ] File deletion
  - [ ] File listing
- [ ] **2.4.3** Create `get_storage_service()` factory function
- [ ] **2.4.4** Write unit tests for Storage service

---

## Phase 3: Tools Implementation
**Status: NOT STARTED**
**Estimated Time: 5-6 hours**

### 3.1 Create Tools Directory
- [ ] **3.1.1** Create `backend/tools/` directory
- [ ] **3.1.2** Create `backend/tools/__init__.py` with exports

### 3.2 Contract Tools
- [ ] **3.2.1** Create `backend/tools/contract_tools.py`
- [ ] **3.2.2** Define `CONTRACT_TOOL_DEFINITIONS` list
- [ ] **3.2.3** Implement `ContractTools` class with:
  - [ ] `get_contract_by_id()` - Retrieve contract with clauses
  - [ ] `search_contracts()` - Search with filters
  - [ ] `save_contract()` - Create/update contracts
- [ ] **3.2.4** Write unit tests

### 3.3 Clause Tools
- [ ] **3.3.1** Create `backend/tools/clause_tools.py`
- [ ] **3.3.2** Define `CLAUSE_TOOL_DEFINITIONS` list
- [ ] **3.3.3** Implement `ClauseTools` class with:
  - [ ] `extract_clauses()` - Parse contract text into clauses
  - [ ] `get_clause_by_type()` - Get specific clause types
  - [ ] `save_clauses()` - Store extracted clauses
- [ ] **3.3.4** Write unit tests

### 3.4 Compliance Tools
- [ ] **3.4.1** Create `backend/tools/compliance_tools.py`
- [ ] **3.4.2** Define `COMPLIANCE_TOOL_DEFINITIONS` list
- [ ] **3.4.3** Implement `ComplianceTools` class with:
  - [ ] `check_gdpr_compliance()` - GDPR checklist
  - [ ] `check_hipaa_compliance()` - HIPAA checklist
  - [ ] `get_compliance_rules()` - Get rules by regulation
  - [ ] `get_applicable_regulations()` - Determine which apply
- [ ] **3.4.4** Write unit tests

### 3.5 Risk Tools
- [ ] **3.5.1** Create `backend/tools/risk_tools.py`
- [ ] **3.5.2** Define `RISK_TOOL_DEFINITIONS` list
- [ ] **3.5.3** Implement `RiskTools` class with:
  - [ ] `calculate_clause_risk()` - Score individual clauses
  - [ ] `get_risk_benchmarks()` - Industry benchmarks
  - [ ] `calculate_overall_risk()` - Aggregate risk score
- [ ] **3.5.4** Write unit tests

### 3.6 Document Tools
- [ ] **3.6.1** Create `backend/tools/document_tools.py`
- [ ] **3.6.2** Define `DOCUMENT_TOOL_DEFINITIONS` list
- [ ] **3.6.3** Implement `DocumentTools` class with:
  - [ ] `save_legal_document()` - Generate and save Word/PDF
  - [ ] `get_document_template()` - Get memo templates
  - [ ] `list_documents()` - List generated documents
- [ ] **3.6.4** Update document templates for legal format
- [ ] **3.6.5** Write unit tests

### 3.7 Logging Tools
- [ ] **3.7.1** Create `backend/tools/logging_tools.py`
- [ ] **3.7.2** Define `LOGGING_TOOL_DEFINITIONS` list
- [ ] **3.7.3** Implement `LoggingTools` class with:
  - [ ] `log_agent_thinking()` - Store thinking process
  - [ ] `get_session_history()` - Retrieve conversation
- [ ] **3.7.4** Write unit tests

---

## Phase 4: Agent Definitions
**Status: NOT STARTED**
**Estimated Time: 3-4 hours**

### 4.1 Agent Definitions File
- [ ] **4.1.1** Completely rewrite `backend/agents/agent_definitions.py`
- [ ] **4.1.2** Define agent name constants:
  - [ ] `CONTRACT_PARSER_AGENT`
  - [ ] `LEGAL_RESEARCH_AGENT`
  - [ ] `COMPLIANCE_CHECKER_AGENT`
  - [ ] `RISK_ASSESSMENT_AGENT`
  - [ ] `LEGAL_MEMO_AGENT`
  - [ ] `ASSISTANT_AGENT`
- [ ] **4.1.3** Write `get_contract_parser_agent_instructions()`
- [ ] **4.1.4** Write `get_legal_research_agent_instructions()`
- [ ] **4.1.5** Write `get_compliance_checker_agent_instructions()`
- [ ] **4.1.6** Write `get_risk_assessment_agent_instructions()`
- [ ] **4.1.7** Write `get_legal_memo_agent_instructions()`
- [ ] **4.1.8** Write `get_assistant_agent_instructions()`
- [ ] **4.1.9** Create `get_agent_instructions()` factory function

### 4.2 Agent Strategies
- [ ] **4.2.1** Rewrite `backend/agents/agent_strategies.py`
- [ ] **4.2.2** Create `QueryAnalyzer` class for query classification
- [ ] **4.2.3** Create `AgentSelector` class for agent routing
- [ ] **4.2.4** Define keyword mappings for legal queries:
  - [ ] Contract analysis keywords
  - [ ] Legal research keywords
  - [ ] Compliance keywords
  - [ ] Risk assessment keywords
  - [ ] Report generation keywords
- [ ] **4.2.5** Implement agent flow logic:
  - [ ] Contract analysis flow
  - [ ] Legal research flow
  - [ ] Compliance check flow
  - [ ] Full analysis flow

### 4.3 Agent Manager
- [ ] **4.3.1** Rewrite `backend/agents/agent_manager.py`
- [ ] **4.3.2** Remove Azure AI agent code
- [ ] **4.3.3** Create Gemini-based agent creation:
  - [ ] `create_agent()` - Create Gemini model with tools
  - [ ] `get_agent_tools()` - Get tools for specific agent
  - [ ] `should_enable_search()` - Determine if agent needs search

---

## Phase 5: Chat Manager Implementation
**Status: NOT STARTED**
**Estimated Time: 6-8 hours**

### 5.1 Legal Chat Manager
- [ ] **5.1.1** Create `backend/managers/legal_chat_manager.py`
- [ ] **5.1.2** Remove old `chatbot_manager.py` or rename as backup
- [ ] **5.1.3** Implement `LegalChatManager` class with:

#### Session Management
- [ ] **5.1.4** `create_session()` - Create new chat session
- [ ] **5.1.5** `get_or_create_session()` - Get existing or create new
- [ ] **5.1.6** `close_session()` - Clean up session resources

#### Message Processing
- [ ] **5.1.7** `process_message()` - Main entry point
- [ ] **5.1.8** `_analyze_query()` - Determine query type and intent
- [ ] **5.1.9** `_select_agents()` - Choose agent sequence
- [ ] **5.1.10** `_execute_agent_flow()` - Run agents in sequence

#### Agent Execution
- [ ] **5.1.11** `_run_agent()` - Execute single agent with Gemini
- [ ] **5.1.12** `_handle_tool_calls()` - Process tool invocations
- [ ] **5.1.13** `_format_response()` - Format final response

#### Contract Processing
- [ ] **5.1.14** `_extract_contract_text()` - Get text from PDF
- [ ] **5.1.15** `_process_contract_upload()` - Handle new contracts

#### History Management
- [ ] **5.1.16** `_build_chat_history()` - Build Gemini history format
- [ ] **5.1.17** `_save_message()` - Store message to Firestore

### 5.2 Rate Limiting
- [ ] **5.2.1** Implement rate limiter for Gemini API
- [ ] **5.2.2** Handle quota exceeded errors gracefully

### 5.3 Error Handling
- [ ] **5.3.1** Implement comprehensive error handling
- [ ] **5.3.2** Add retry logic for transient failures
- [ ] **5.3.3** Create user-friendly error messages

---

## Phase 6: API Layer Updates
**Status: NOT STARTED**
**Estimated Time: 3-4 hours**

### 6.1 Main Application
- [ ] **6.1.1** Update `backend/main.py`:
  - [ ] Remove Azure-specific imports
  - [ ] Update initialization for Google services
  - [ ] Keep FastAPI setup
- [ ] **6.1.2** Update `backend/api/app.py`:
  - [ ] Update CORS settings
  - [ ] Add new routers

### 6.2 API Endpoints
- [ ] **6.2.1** Rewrite `backend/api/endpoints.py`
- [ ] **6.2.2** Implement chat endpoints:
  - [ ] `POST /api/chat` - Send message
  - [ ] `GET /api/chat/sessions` - List sessions
  - [ ] `GET /api/chat/sessions/{id}` - Get session
  - [ ] `DELETE /api/chat/sessions/{id}` - Delete session
- [ ] **6.2.3** Implement contract endpoints:
  - [ ] `POST /api/contracts` - Upload contract
  - [ ] `GET /api/contracts` - List contracts
  - [ ] `GET /api/contracts/{id}` - Get contract
  - [ ] `DELETE /api/contracts/{id}` - Delete contract
  - [ ] `GET /api/contracts/{id}/clauses` - Get clauses
- [ ] **6.2.4** Implement compliance endpoints:
  - [ ] `GET /api/compliance/rules/{regulation}` - Get rules
- [ ] **6.2.5** Implement document endpoints:
  - [ ] `GET /api/documents` - List documents
  - [ ] `GET /api/documents/{id}/download` - Download
- [ ] **6.2.6** Implement thinking logs endpoints:
  - [ ] `GET /api/thinking-logs` - List logs
- [ ] **6.2.7** Implement dashboard endpoints:
  - [ ] `GET /api/dashboard/stats` - Get statistics

### 6.3 API Models
- [ ] **6.3.1** Create Pydantic models for requests/responses
- [ ] **6.3.2** Add validation for all inputs

---

## Phase 7: Frontend Updates
**Status: NOT STARTED**
**Estimated Time: 6-8 hours**

### 7.1 Update Existing Pages

#### Chat Page (`frontend/app/chat/page.tsx`)
- [ ] **7.1.1** Add PDF upload functionality
- [ ] **7.1.2** Update API calls to new endpoints
- [ ] **7.1.3** Add citation display in messages
- [ ] **7.1.4** Update markdown rendering for legal format
- [ ] **7.1.5** Add contract context indicator
- [ ] **7.1.6** Style updates for legal theme

#### Dashboard Page (`frontend/app/dashboard/page.tsx`)
- [ ] **7.1.7** Replace MapChart with risk distribution chart
- [ ] **7.1.8** Add compliance status overview
- [ ] **7.1.9** Add recent contracts widget
- [ ] **7.1.10** Add key statistics cards
- [ ] **7.1.11** Update API calls

#### Reports/Documents Page (`frontend/app/reports/page.tsx`)
- [ ] **7.1.12** Rename to documents
- [ ] **7.1.13** Update columns for legal documents
- [ ] **7.1.14** Add download functionality
- [ ] **7.1.15** Update API calls

#### Thinking Logs Page (`frontend/app/thinking-logs/page.tsx`)
- [ ] **7.1.16** Update for new agent names
- [ ] **7.1.17** Update columns display
- [ ] **7.1.18** Minor styling updates

### 7.2 Create New Pages

#### Contracts Page (`frontend/app/contracts/page.tsx`)
- [ ] **7.2.1** Create contracts list page
- [ ] **7.2.2** Add filter and search
- [ ] **7.2.3** Create contract card component
- [ ] **7.2.4** Add upload button linking to upload page

#### Contract Detail Page (`frontend/app/contracts/[id]/page.tsx`)
- [ ] **7.2.5** Create contract detail view
- [ ] **7.2.6** Display contract metadata
- [ ] **7.2.7** Create clauses list with risk badges
- [ ] **7.2.8** Add compliance status panel
- [ ] **7.2.9** Add "Analyze" action buttons

#### Contract Upload Page (`frontend/app/contracts/upload/page.tsx`)
- [ ] **7.2.10** Create upload page with drag-drop
- [ ] **7.2.11** Add progress indicator
- [ ] **7.2.12** Redirect to analysis after upload

### 7.3 New Components

- [ ] **7.3.1** Create `components/contract-upload.tsx` - Drag-drop upload
- [ ] **7.3.2** Create `components/contract-card.tsx` - Contract list item
- [ ] **7.3.3** Create `components/clause-card.tsx` - Clause display
- [ ] **7.3.4** Create `components/risk-badge.tsx` - Risk score badge
- [ ] **7.3.5** Create `components/risk-chart.tsx` - Risk distribution chart
- [ ] **7.3.6** Create `components/compliance-checklist.tsx` - Compliance status
- [ ] **7.3.7** Create `components/citation-link.tsx` - Legal citation display

### 7.4 Update Sidebar and Navigation
- [ ] **7.4.1** Update `components/app-sidebar.tsx`:
  - [ ] Add "Contracts" navigation item
  - [ ] Update icons and labels
  - [ ] Update branding to "LegalMind"
- [ ] **7.4.2** Update page titles and breadcrumbs

### 7.5 API Route Updates (`frontend/app/api/`)
- [ ] **7.5.1** Update `chat/route.ts` for new backend
- [ ] **7.5.2** Create `contracts/route.ts`
- [ ] **7.5.3** Create `documents/route.ts`
- [ ] **7.5.4** Update other API routes as needed

---

## Phase 8: Data & Templates
**Status: NOT STARTED**
**Estimated Time: 2-3 hours**

### 8.1 Document Templates
- [ ] **8.1.1** Create `backend/templates/` directory
- [ ] **8.1.2** Create `legal_memo.md` template
- [ ] **8.1.3** Create `contract_summary.md` template
- [ ] **8.1.4** Create `compliance_report.md` template
- [ ] **8.1.5** Create `executive_summary.md` template

### 8.2 Seed Data
- [ ] **8.2.1** Create Firestore seed script
- [ ] **8.2.2** Add compliance rules data:
  - [ ] GDPR rules
  - [ ] HIPAA rules
  - [ ] CCPA rules
- [ ] **8.2.3** Add sample contracts for testing
- [ ] **8.2.4** Run seed script

### 8.3 Test Data
- [ ] **8.3.1** Create sample NDA PDF
- [ ] **8.3.2** Create sample MSA PDF
- [ ] **8.3.3** Create sample employment contract PDF
- [ ] **8.3.4** Create GDPR-compliant sample
- [ ] **8.3.5** Create GDPR-violating sample (for testing)

---

## Phase 9: Cleanup & Removal
**Status: NOT STARTED**
**Estimated Time: 1-2 hours**

### 9.1 Remove Azure-Specific Files
- [ ] **9.1.1** Delete `backend/streamlit_app.py`
- [ ] **9.1.2** Delete `backend/sql/` directory
- [ ] **9.1.3** Delete `backend/test_scripts/test_azure_storage.py`
- [ ] **9.1.4** Delete `backend/test_scripts/full_test_bing_agent.py`

### 9.2 Remove Old Plugins
- [ ] **9.2.1** Delete `backend/plugins/schedule_plugin.py`
- [ ] **9.2.2** Delete `backend/plugins/political_risk_json_plugin.py`
- [ ] **9.2.3** Delete `backend/plugins/citation_handler_plugin.py`
- [ ] **9.2.4** Update `backend/plugins/__init__.py`

### 9.3 Clean Up Old Code
- [ ] **9.3.1** Remove Azure imports from all files
- [ ] **9.3.2** Remove Semantic Kernel imports
- [ ] **9.3.3** Remove old manager files or archive them

### 9.4 Update Documentation
- [ ] **9.4.1** Update main `README.md` for LegalMind
- [ ] **9.4.2** Update `backend/README.md`
- [ ] **9.4.3** Update `frontend/README.md`
- [x] **9.4.4** Remove references to Azure/legacy branding

---

## Phase 10: Testing & Validation
**Status: NOT STARTED**
**Estimated Time: 4-6 hours**

### 10.1 Unit Tests
- [ ] **10.1.1** Test Gemini service
- [ ] **10.1.2** Test Firestore service
- [ ] **10.1.3** Test Storage service
- [ ] **10.1.4** Test all tools
- [ ] **10.1.5** Test agent definitions

### 10.2 Integration Tests
- [ ] **10.2.1** Test contract upload flow
- [ ] **10.2.2** Test chat conversation flow
- [ ] **10.2.3** Test multi-agent collaboration
- [ ] **10.2.4** Test document generation
- [ ] **10.2.5** Test legal research with citations

### 10.3 End-to-End Tests
- [ ] **10.3.1** Test: Upload NDA → Analyze → Get Report
- [ ] **10.3.2** Test: Legal research question → Cited response
- [ ] **10.3.3** Test: Compliance check → GDPR report
- [ ] **10.3.4** Test: Full contract review workflow

### 10.4 Manual Testing
- [ ] **10.4.1** Test all chat scenarios
- [ ] **10.4.2** Test all UI interactions
- [ ] **10.4.3** Test edge cases and error handling
- [ ] **10.4.4** Test on different browsers

---

## Phase 11: Deployment
**Status: NOT STARTED**
**Estimated Time: 3-4 hours**

### 11.1 Google Cloud Setup
- [ ] **11.1.1** Create Firestore database
- [ ] **11.1.2** Create Cloud Storage bucket
- [ ] **11.1.3** Set up Secret Manager with API keys
- [ ] **11.1.4** Configure IAM permissions

### 11.2 Backend Deployment (Cloud Run)
- [ ] **11.2.1** Create `Dockerfile` for backend
- [ ] **11.2.2** Create `cloudbuild.yaml`
- [ ] **11.2.3** Configure Cloud Run service
- [ ] **11.2.4** Set environment variables
- [ ] **11.2.5** Deploy and test

### 11.3 Frontend Deployment (Firebase)
- [ ] **11.3.1** Initialize Firebase in project
- [ ] **11.3.2** Configure `firebase.json`
- [ ] **11.3.3** Update API URLs for production
- [ ] **11.3.4** Build production frontend
- [ ] **11.3.5** Deploy to Firebase Hosting

### 11.4 Final Configuration
- [ ] **11.4.1** Set up custom domain (optional)
- [ ] **11.4.2** Configure CORS for production
- [ ] **11.4.3** Test production deployment
- [ ] **11.4.4** Monitor for errors

---

## Phase 12: Documentation & Polish
**Status: NOT STARTED**
**Estimated Time: 2-3 hours**

### 12.1 User Documentation
- [ ] **12.1.1** Write user guide
- [ ] **12.1.2** Create feature walkthrough
- [ ] **12.1.3** Document supported contract types
- [ ] **12.1.4** Document compliance frameworks

### 12.2 Technical Documentation
- [ ] **12.2.1** Document API endpoints (OpenAPI/Swagger)
- [ ] **12.2.2** Document agent architecture
- [ ] **12.2.3** Document tool specifications
- [ ] **12.2.4** Create development setup guide

### 12.3 Hackathon Submission
- [ ] **12.3.1** Create demo video
- [ ] **12.3.2** Prepare presentation slides
- [ ] **12.3.3** Write project description
- [ ] **12.3.4** Highlight Gemini features used:
  - [ ] 1M+ token context
  - [ ] Google Search Grounding
  - [ ] Function calling
  - [ ] Structured output
- [ ] **12.3.5** Final submission

---

## Summary

| Phase | Tasks | Status | Est. Hours |
|-------|-------|--------|------------|
| 1. Setup | 17 | ⬜ Not Started | 2-3 |
| 2. Services | 16 | ⬜ Not Started | 4-5 |
| 3. Tools | 28 | ⬜ Not Started | 5-6 |
| 4. Agents | 15 | ⬜ Not Started | 3-4 |
| 5. Chat Manager | 20 | ⬜ Not Started | 6-8 |
| 6. API Layer | 15 | ⬜ Not Started | 3-4 |
| 7. Frontend | 31 | ⬜ Not Started | 6-8 |
| 8. Data/Templates | 13 | ⬜ Not Started | 2-3 |
| 9. Cleanup | 12 | ⬜ Not Started | 1-2 |
| 10. Testing | 17 | ⬜ Not Started | 4-6 |
| 11. Deployment | 14 | ⬜ Not Started | 3-4 |
| 12. Documentation | 14 | ⬜ Not Started | 2-3 |
| **TOTAL** | **212** | | **42-56 hrs** |

---

## Quick Start Checklist

For immediate development, complete these tasks first:

1. [ ] Create `.env` with `GEMINI_API_KEY`
2. [ ] Install Google Cloud dependencies
3. [ ] Create `gemini_service.py`
4. [ ] Create `agent_definitions.py` with legal agents
5. [ ] Create basic `legal_chat_manager.py`
6. [ ] Test single agent conversation
7. [ ] Add multi-agent flow
8. [ ] Update frontend chat page
9. [ ] Deploy MVP

---

## Notes

- **Priority**: Phases 1-5 are critical path, must be done sequentially
- **Parallelizable**: Frontend work (Phase 7) can start after Phase 2
- **Dependencies**: Phase 6 depends on Phases 2-5
- **Testing**: Continuous testing throughout, not just Phase 10
- **Documentation**: Update as you go, don't leave for end
