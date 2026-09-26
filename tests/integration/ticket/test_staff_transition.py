from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.audit.writer import AuditWriter
from campus247.application.ticket.transition import (
    StaffTicketTransitionService,
    TicketTransitionCommand,
)
from campus247.domain.policy.staff import StaffPolicyEngine
from campus247.domain.ticket.model import Ticket, TicketCategory, TicketPriority, TicketStatus
from campus247.ports.identity import IdentityContext, IdentityRole


@pytest.fixture
def staff_actor() -> IdentityContext:
    now = datetime.now(timezone.utc)
    return IdentityContext(
        subject_id="01923456-789a-7def-8123-456789abcde2",
        external_subject="syn_staff_1",
        issuer="urn:campus247:issuer:synthetic",
        roles=(IdentityRole.SUPPORT_OFFICER,),
        display_name="Cán bộ Hỗ trợ",
        unit_ids=("UNIT_GENERAL",),
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )


@pytest.fixture
def service():
    policy_engine = StaffPolicyEngine()
    audit_writer = AuditWriter()
    store: dict[str, Ticket] = {}
    svc = StaffTicketTransitionService(tickets=store, policy_engine=policy_engine, audit_writer=audit_writer)
    return svc, store, audit_writer


@pytest.mark.asyncio
async def test_staff_assign_ticket(service, staff_actor):
    svc, store, audit_writer = service
    now = datetime.now(timezone.utc)

    # Create OPEN ticket
    ticket = Ticket.create_draft(
        requester_user_id="01923456-789a-7def-8123-456789abcde1",
        category=TicketCategory.GENERAL_SUPPORT,
        priority=TicketPriority.NORMAL,
        subject="Cần hỗ trợ",
        description="Chi tiết",
        queue_key="UNIT_GENERAL",
    ).request_confirmation().confirm_create()
    store[ticket.id] = ticket

    cmd = TicketTransitionCommand(
        ticket_id=ticket.id,
        target_status="ASSIGNED",
        actor=staff_actor,
        assigned_user_id=staff_actor.subject_id,
    )
    res = await svc.transition_ticket(cmd)
    assert res.status == TicketStatus.ASSIGNED
    assert res.assigned_user_id == staff_actor.subject_id
    assert res.version == 4
    assert len(audit_writer._log) == 1


@pytest.mark.asyncio
async def test_staff_full_resolution_flow(service, staff_actor):
    svc, store, _ = service

    ticket = Ticket.create_draft(
        requester_user_id="01923456-789a-7def-8123-456789abcde1",
        category=TicketCategory.GENERAL_SUPPORT,
        priority=TicketPriority.NORMAL,
        subject="Cần hỗ trợ",
        description="Chi tiết",
        queue_key="UNIT_GENERAL",
    ).request_confirmation().confirm_create()
    store[ticket.id] = ticket

    # 1. Assign
    await svc.transition_ticket(
        TicketTransitionCommand(
            ticket_id=ticket.id,
            target_status="ASSIGNED",
            actor=staff_actor,
            assigned_user_id=staff_actor.subject_id,
        )
    )

    # 2. In Progress
    t_prog = await svc.transition_ticket(
        TicketTransitionCommand(ticket_id=ticket.id, target_status="IN_PROGRESS", actor=staff_actor)
    )
    assert t_prog.status == TicketStatus.IN_PROGRESS

    # 3. Resolve
    t_res = await svc.transition_ticket(
        TicketTransitionCommand(
            ticket_id=ticket.id,
            target_status="RESOLVED",
            actor=staff_actor,
            resolution_code="ANSWERED",
            resolution_summary="Đã hướng dẫn sinh viên đăng ký",
        )
    )
    assert t_res.status == TicketStatus.RESOLVED

    # 4. Close
    t_closed = await svc.transition_ticket(
        TicketTransitionCommand(ticket_id=ticket.id, target_status="CLOSED", actor=staff_actor)
    )
    assert t_closed.status == TicketStatus.CLOSED


@pytest.mark.asyncio
async def test_staff_policy_denial_unauthorized_unit(service):
    svc, store, _ = service
    now = datetime.now(timezone.utc)

    other_staff = IdentityContext(
        subject_id="01923456-789a-7def-8123-456789abcde3",
        external_subject="syn_staff_2",
        issuer="urn:campus247:issuer:synthetic",
        roles=(IdentityRole.SUPPORT_OFFICER,),
        display_name="Cán bộ Khác",
        unit_ids=("UNIT_OTHER",),
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )

    ticket = Ticket.create_draft(
        requester_user_id="01923456-789a-7def-8123-456789abcde1",
        category=TicketCategory.GENERAL_SUPPORT,
        priority=TicketPriority.NORMAL,
        subject="Cần hỗ trợ",
        description="Chi tiết",
        queue_key="UNIT_GENERAL",
    ).request_confirmation().confirm_create()
    store[ticket.id] = ticket

    cmd = TicketTransitionCommand(
        ticket_id=ticket.id,
        target_status="ASSIGNED",
        actor=other_staff,
        assigned_user_id=other_staff.subject_id,
    )
    with pytest.raises(PermissionError, match="Action not permitted"):
        await svc.transition_ticket(cmd)
