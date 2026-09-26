from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from campus247.agent.graph import CampusAgentWorkflow
from campus247.application.action.idempotency import IdempotencyLedger
from campus247.presentation.errors import (
    http_exception_handler,
    validation_exception_handler,
)
from campus247.application.audit.writer import AuditWriter
from campus247.application.booking.availability import ExistingBooking, RoomInfo
from campus247.application.conversation.messages import ConversationMessageService
from campus247.application.conversations.feedback import FeedbackService
from campus247.application.identity.logout import InMemoryRevocationStore, LogoutService
from campus247.application.privacy.consent import PrivacyConsentService, PrivacyNoticeConfig
from campus247.application.privacy.requests import PrivacyRequestService
from campus247.application.ticket.confirm import TicketConfirmationService
from campus247.application.ticket.preview import TicketPreviewService
from campus247.bootstrap.settings import get_settings
from campus247.domain.action.confirmation import ConfirmationTokenService
from campus247.domain.policy.student import StudentPolicyEngine
from campus247.domain.shared.values import generate_uuid7
from campus247.infrastructure.db import get_engine
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.infrastructure.llm.factory import create_llm_gateway
from campus247.infrastructure.retrieval.hybrid import HybridSearchAdapter
from campus247.infrastructure.retrieval.lexical import LexicalSearchAdapter
from campus247.infrastructure.retrieval.vector import VectorSearchAdapter
from campus247.agent.nodes.definitions import run_sync
from campus247.infrastructure.schedule.synthetic import SyntheticScheduleAdapter
from campus247.presentation import (
    capabilities,
    chat,
    document_requests,
    feedback,
    handovers,
    health,
    identity,
    knowledge,
    logout,
    privacy_notice,
    privacy_requests,
    rooms,
    schedule,
    ticket_queries,
    tickets,
)
from campus247.presentation.capabilities import CapabilityManager
from campus247.presentation.identity import IdentityMiddleware


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Assign X-Request-Id header and state attribute to every incoming request."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("x-request-id") or generate_uuid7()
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database engine startup and shutdown."""
    settings = get_settings()
    engine = None
    try:
        engine = get_engine(settings.DATABASE_URL)
        app.state.db_engine = engine
    except Exception:
        pass
    yield
    if engine is not None:
        try:
            await engine.dispose()
        except Exception:
            pass


def create_app() -> FastAPI:
    """Application factory for Campus 24/7 FastAPI backend service."""
    settings = get_settings()
    app = FastAPI(
        title="Campus 24/7 API",
        version="0.1.0",
        description="Campus 24/7 — HUCE Demo backend application API",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # 1. Request ID Middleware
    app.add_middleware(RequestIdMiddleware)

    # Register RFC 9457 Problem Details Exception Handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    # 2. Synthetic Identity Middleware for Demo Mode
    identity_adapter = SyntheticIdentityAdapter(
        secret_key=settings.IDENTITY_SECRET_KEY,
        environment="local",
    )
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    # 3. CORS Middleware for Local Frontend Development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize shared services and stores for demo mode
    conv_service = ConversationMessageService()
    policy_engine = StudentPolicyEngine()
    schedule_adapter = SyntheticScheduleAdapter()

    token_svc = ConfirmationTokenService(signing_key=settings.CONFIRMATION_SIGNING_KEY)
    preview_svc = TicketPreviewService(confirmation_service=token_svc, policy_engine=policy_engine)
    idempotency_ledger = IdempotencyLedger()
    audit_writer = AuditWriter()
    confirm_svc = TicketConfirmationService(
        confirmation_service=token_svc,
        idempotency_ledger=idempotency_ledger,
        audit_writer=audit_writer,
    )

    ticket_store: dict[str, Any] = {}
    doc_store: dict[str, Any] = {}
    handover_store: dict[str, Any] = {}
    sources_store: dict[str, Any] = {}
    versions_store: dict[str, Any] = {}

    rooms_list = [
        RoomInfo(
            id="01923456-789a-7def-8123-456789abcde1",
            room_code="H1-301",
            display_name="Phòng 301 - Giảng đường H1",
            capacity=50,
            features=("WIFI", "PROJECTOR"),
        ),
        RoomInfo(
            id="01923456-789a-7def-8123-456789abcde2",
            room_code="H1-302",
            display_name="Phòng 302 - Giảng đường H1",
            capacity=25,
            features=("WIFI",),
        ),
        RoomInfo(
            id="01923456-789a-7def-8123-456789abcde3",
            room_code="H2-101",
            display_name="Hội trường H2",
            capacity=150,
            features=("PROJECTOR", "MIC", "STAGE"),
        ),
    ]
    bookings_list: list[ExistingBooking] = []

    feedback_service = FeedbackService(conv_service=conv_service)

    notice = PrivacyNoticeConfig(
        notice_id=generate_uuid7(),
        version="1.0.0",
        effective_at=datetime.now(timezone.utc),
        status="ACTIVE",
        disclaimer={"statement": "HUCE demo synthetic data only"},
        data_categories=["ACCOUNT_CONTEXT", "CONVERSATION_CONTENT", "REQUEST_METADATA", "AUDIT_METADATA"],
        purposes=["SERVICE_DELIVERY", "SAFETY_HANDOVER", "QUALITY_FEEDBACK", "SECURITY_AUDIT"],
        retention_summary=[{"data_class": "ACCOUNT_CONTEXT", "configured_rule": "PRIV-RET-001"}],
    )
    consent_service = PrivacyConsentService(active_notice=notice, audit_writer=audit_writer)
    privacy_request_service = PrivacyRequestService(audit_writer=audit_writer)
    logout_service = LogoutService(revocation_store=InMemoryRevocationStore())
    capability_manager = CapabilityManager()

    # Mount all 15 presentation routers
    # Health: /health/live, /health/ready
    app.include_router(health.router)

    # Identity: /v1/users/me
    app.include_router(identity.create_identity_router())

    llm_gateway = create_llm_gateway(settings=settings)
    vec_adapter = VectorSearchAdapter()
    lex_adapter = LexicalSearchAdapter()
    hybrid_adapter = HybridSearchAdapter(vec_adapter, lex_adapter, fusion_k=10)

    def search_knowledge(query: str) -> list[dict[str, Any]]:
        try:
            candidates = run_sync(hybrid_adapter.search(query, top_k=10))
            return [
                {
                    "chunk_id": c.chunk_id,
                    "document_version_id": c.document_version_id,
                    "section_path": c.section_path,
                    "content_text": c.content_text,
                    "score": c.score,
                }
                for c in candidates
            ]
        except Exception:
            return []

    agent_workflow = CampusAgentWorkflow(search_fn=search_knowledge, llm_gateway=llm_gateway)

    # Chat / Conversations: /v1/conversations/{conversation_id}/messages:stream
    app.include_router(chat.create_chat_router(conv_service=conv_service, agent_runner=agent_workflow))

    # Schedule: /v1/students/me/schedule
    app.include_router(schedule.create_schedule_router(schedule_adapter=schedule_adapter, policy_engine=policy_engine))

    # Tickets preview & confirm: /v1/tickets/preview, /v1/tickets/{preview_id}/confirm
    app.include_router(tickets.create_ticket_router(preview_svc=preview_svc, confirm_svc=confirm_svc))

    # Ticket queries: /v1/tickets, /v1/tickets/{ticket_id}
    app.include_router(ticket_queries.create_ticket_query_router(store=ticket_store))

    # Rooms & availability: /v1/rooms, /v1/rooms/{room_id}/availability
    app.include_router(rooms.create_rooms_router(rooms=rooms_list, bookings=bookings_list))

    # Knowledge: /v1/knowledge/sources, /v1/knowledge/document-versions/{id}
    app.include_router(knowledge.create_knowledge_router(sources=sources_store, versions=versions_store))

    # Document requests: /v1/document-requests, /v1/document-requests/{id}
    app.include_router(document_requests.create_document_request_router(store=doc_store))

    # Handovers: /v1/staff/handovers, /v1/handovers/{id}
    app.include_router(handovers.create_handover_router(store=handover_store))

    # Answer feedback: /v1/conversations/{conversation_id}/messages/{message_id}/feedback
    app.include_router(feedback.create_feedback_router(feedback_service=feedback_service))

    # Privacy notice & consents: /v1/privacy/notice, /v1/privacy/consents
    app.include_router(privacy_notice.create_privacy_router(consent_service=consent_service))

    # Privacy requests: /v1/privacy/requests, /v1/privacy/requests/{id}
    app.include_router(privacy_requests.create_privacy_request_router(service=privacy_request_service))

    # Capabilities: /v1/capabilities, /v1/operations/capabilities
    app.include_router(capabilities.create_capabilities_router(manager=capability_manager))

    # Logout: /v1/auth/logout & /v1/logout
    app.include_router(logout.create_logout_router(logout_service=logout_service), prefix="/v1/auth")
    app.include_router(logout.create_logout_router(logout_service=logout_service), prefix="/v1")

    return app

