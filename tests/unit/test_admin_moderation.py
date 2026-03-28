"""Tests for admin moderation API."""

import pytest
from fastapi import HTTPException
from src.api.admin_moderation import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    SAMPLE_CAMPAIGNS,
    SAMPLE_FLAGS,
    SAMPLE_RESCUERS,
    BulkActionType,
    CampaignStatus,
    FlagReason,
    FlagStatus,
    ModerationAction,
    RescuerStatus,
    VerificationStatus,
    _reset_store,
    bulk_action,
    flag_rescuer,
    get_moderation_history,
    list_campaigns,
    list_flags,
    list_rescuers,
    review_campaign,
    review_flag,
    router,
    suspend_rescuer,
    verify_rescuer,
)


@pytest.fixture(autouse=True)
def _clean_store():
    """Reset in-memory stores before each test."""
    _reset_store()
    yield
    _reset_store()


# -- Enum tests --------------------------------------------------------------


class TestEnums:
    def test_rescuer_status_values(self):
        assert RescuerStatus.ACTIVE == "active"
        assert RescuerStatus.SUSPENDED == "suspended"
        assert RescuerStatus.PENDING == "pending"

    def test_verification_status_values(self):
        assert VerificationStatus.VERIFIED == "verified"
        assert VerificationStatus.UNVERIFIED == "unverified"
        assert VerificationStatus.UNDER_REVIEW == "under_review"

    def test_moderation_action_values(self):
        assert ModerationAction.VERIFY == "verify"
        assert ModerationAction.SUSPEND == "suspend"
        assert ModerationAction.APPROVE_CAMPAIGN == "approve_campaign"

    def test_campaign_status_values(self):
        assert CampaignStatus.PENDING == "pending"
        assert CampaignStatus.APPROVED == "approved"
        assert CampaignStatus.REJECTED == "rejected"

    def test_flag_status_values(self):
        assert FlagStatus.OPEN == "open"
        assert FlagStatus.ACTION_TAKEN == "action_taken"

    def test_flag_reason_values(self):
        assert FlagReason.INAPPROPRIATE == "inappropriate"
        assert FlagReason.SPAM == "spam"

    def test_bulk_action_values(self):
        assert BulkActionType.VERIFY == "verify"
        assert BulkActionType.SUSPEND == "suspend"


# -- Constants tests ----------------------------------------------------------


class TestConstants:
    def test_default_page_size(self):
        assert DEFAULT_PAGE_SIZE == 20

    def test_max_page_size(self):
        assert MAX_PAGE_SIZE == 100

    def test_sample_rescuers_not_empty(self):
        assert len(SAMPLE_RESCUERS) > 0

    def test_sample_campaigns_not_empty(self):
        assert len(SAMPLE_CAMPAIGNS) > 0

    def test_sample_flags_not_empty(self):
        assert len(SAMPLE_FLAGS) > 0


# -- Router tests -------------------------------------------------------------


class TestRouter:
    def test_router_prefix(self):
        assert router.prefix == "/api/admin/moderation"

    def test_router_tags(self):
        assert "admin-moderation" in router.tags


# -- Rescuer list tests -------------------------------------------------------


class TestListRescuers:
    @pytest.mark.asyncio
    async def test_returns_all_rescuers(self):
        result = await list_rescuers(status_filter=None, verification=None, page=1, page_size=20)
        assert result.total == len(SAMPLE_RESCUERS)
        assert len(result.rescuers) == len(SAMPLE_RESCUERS)

    @pytest.mark.asyncio
    async def test_search_by_name(self):
        result = await list_rescuers(
            search="Carlos", status_filter=None, verification=None, page=1, page_size=20
        )
        assert result.total == 1
        assert result.rescuers[0].name == "Carlos Mendoza"

    @pytest.mark.asyncio
    async def test_search_by_email(self):
        result = await list_rescuers(
            search="protectora", status_filter=None, verification=None, page=1, page_size=20
        )
        assert result.total == 1
        assert result.rescuers[0].name == "Ana Benitez"

    @pytest.mark.asyncio
    async def test_filter_by_status(self):
        result = await list_rescuers(
            status_filter=RescuerStatus.SUSPENDED, verification=None, page=1, page_size=20
        )
        assert result.total == 1
        assert result.rescuers[0].status == RescuerStatus.SUSPENDED

    @pytest.mark.asyncio
    async def test_filter_by_verification(self):
        result = await list_rescuers(
            search=None,
            status_filter=None,
            verification=VerificationStatus.VERIFIED,
            page=1,
            page_size=20,
        )
        assert result.total == 2
        for r in result.rescuers:
            assert r.verification_status == VerificationStatus.VERIFIED

    @pytest.mark.asyncio
    async def test_pagination(self):
        result = await list_rescuers(status_filter=None, verification=None, page=1, page_size=2)
        assert len(result.rescuers) == 2
        assert result.total == len(SAMPLE_RESCUERS)

    @pytest.mark.asyncio
    async def test_search_no_results(self):
        result = await list_rescuers(
            search="nonexistent", status_filter=None, verification=None, page=1, page_size=20
        )
        assert result.total == 0
        assert len(result.rescuers) == 0


# -- Verify rescuer tests ----------------------------------------------------


class TestVerifyRescuer:
    @pytest.mark.asyncio
    async def test_verify_rescuer(self):
        from src.api.admin_moderation import VerifyRequest

        req = VerifyRequest(verify=True, reason="Documents confirmed")
        result = await verify_rescuer("resc-002", req)
        assert result.success is True
        assert result.action == ModerationAction.VERIFY

    @pytest.mark.asyncio
    async def test_unverify_rescuer(self):
        from src.api.admin_moderation import VerifyRequest

        req = VerifyRequest(verify=False, reason="Documents expired")
        result = await verify_rescuer("resc-001", req)
        assert result.success is True
        assert result.action == ModerationAction.UNVERIFY

    @pytest.mark.asyncio
    async def test_verify_nonexistent_rescuer(self):
        from src.api.admin_moderation import VerifyRequest

        req = VerifyRequest(verify=True, reason="Test")
        with pytest.raises(HTTPException) as exc:
            await verify_rescuer("nonexistent", req)
        assert exc.value.status_code == 404


# -- Suspend rescuer tests ---------------------------------------------------


class TestSuspendRescuer:
    @pytest.mark.asyncio
    async def test_suspend_rescuer(self):
        from src.api.admin_moderation import SuspendRequest

        req = SuspendRequest(suspend=True, reason="Violating policy")
        result = await suspend_rescuer("resc-001", req)
        assert result.success is True
        assert result.action == ModerationAction.SUSPEND

    @pytest.mark.asyncio
    async def test_unsuspend_rescuer(self):
        from src.api.admin_moderation import SuspendRequest

        req = SuspendRequest(suspend=False, reason="Appeal approved")
        result = await suspend_rescuer("resc-003", req)
        assert result.success is True
        assert result.action == ModerationAction.UNSUSPEND


# -- Flag rescuer tests ------------------------------------------------------


class TestFlagRescuer:
    @pytest.mark.asyncio
    async def test_flag_rescuer(self):
        from src.api.admin_moderation import FlagRequest

        req = FlagRequest(reason=FlagReason.MISLEADING, details="Fake photos")
        result = await flag_rescuer("resc-001", req)
        assert result.success is True
        assert result.action == ModerationAction.FLAG


# -- Bulk action tests -------------------------------------------------------


class TestBulkAction:
    @pytest.mark.asyncio
    async def test_bulk_verify(self):
        from src.api.admin_moderation import BulkActionRequest

        req = BulkActionRequest(
            rescuer_ids=["resc-002", "resc-005"],
            action=BulkActionType.VERIFY,
            reason="Batch verification",
        )
        result = await bulk_action(req)
        assert result.processed == 2
        assert result.failed == 0

    @pytest.mark.asyncio
    async def test_bulk_with_invalid_ids(self):
        from src.api.admin_moderation import BulkActionRequest

        req = BulkActionRequest(
            rescuer_ids=["resc-001", "invalid-id"],
            action=BulkActionType.SUSPEND,
            reason="Batch suspend",
        )
        result = await bulk_action(req)
        assert result.processed == 1
        assert result.failed == 1
        assert len(result.errors) == 1


# -- Campaign tests ----------------------------------------------------------


class TestCampaigns:
    @pytest.mark.asyncio
    async def test_list_all_campaigns(self):
        result = await list_campaigns(status_filter=None)
        assert result.total == len(SAMPLE_CAMPAIGNS)

    @pytest.mark.asyncio
    async def test_filter_pending_campaigns(self):
        result = await list_campaigns(status_filter=CampaignStatus.PENDING)
        for c in result.campaigns:
            assert c.status == CampaignStatus.PENDING

    @pytest.mark.asyncio
    async def test_approve_campaign(self):
        from src.api.admin_moderation import CampaignReviewRequest

        req = CampaignReviewRequest(approve=True, reason="Looks good")
        result = await review_campaign("camp-001", req)
        assert result.success is True
        assert result.action == ModerationAction.APPROVE_CAMPAIGN

    @pytest.mark.asyncio
    async def test_reject_campaign(self):
        from src.api.admin_moderation import CampaignReviewRequest

        req = CampaignReviewRequest(approve=False, reason="Incomplete info")
        result = await review_campaign("camp-002", req)
        assert result.success is True
        assert result.action == ModerationAction.REJECT_CAMPAIGN

    @pytest.mark.asyncio
    async def test_review_nonexistent_campaign(self):
        from src.api.admin_moderation import CampaignReviewRequest

        req = CampaignReviewRequest(approve=True, reason="Test")
        with pytest.raises(HTTPException) as exc:
            await review_campaign("nonexistent", req)
        assert exc.value.status_code == 404


# -- Flag tests --------------------------------------------------------------


class TestFlags:
    @pytest.mark.asyncio
    async def test_list_all_flags(self):
        result = await list_flags(status_filter=None)
        assert result.total == len(SAMPLE_FLAGS)

    @pytest.mark.asyncio
    async def test_filter_open_flags(self):
        result = await list_flags(status_filter=FlagStatus.OPEN)
        for f in result.flags:
            assert f.status == FlagStatus.OPEN

    @pytest.mark.asyncio
    async def test_dismiss_flag(self):
        from src.api.admin_moderation import FlagReviewRequest

        req = FlagReviewRequest(action="dismiss", reason="Not a real issue")
        result = await review_flag("flag-001", req)
        assert result.success is True
        assert result.action == ModerationAction.DISMISS_FLAG

    @pytest.mark.asyncio
    async def test_action_on_flag(self):
        from src.api.admin_moderation import FlagReviewRequest

        req = FlagReviewRequest(action="remove_content", reason="Content violated policy")
        result = await review_flag("flag-002", req)
        assert result.success is True
        assert result.action == ModerationAction.REMOVE_CONTENT

    @pytest.mark.asyncio
    async def test_review_nonexistent_flag(self):
        from src.api.admin_moderation import FlagReviewRequest

        req = FlagReviewRequest(action="dismiss", reason="Test")
        with pytest.raises(HTTPException) as exc:
            await review_flag("nonexistent", req)
        assert exc.value.status_code == 404


# -- History tests ------------------------------------------------------------


class TestHistory:
    @pytest.mark.asyncio
    async def test_empty_history(self):
        result = await get_moderation_history(page=1, page_size=20)
        assert result.total == 0
        assert len(result.entries) == 0

    @pytest.mark.asyncio
    async def test_history_after_actions(self):
        from src.api.admin_moderation import VerifyRequest

        req = VerifyRequest(verify=True, reason="Verified")
        await verify_rescuer("resc-002", req)

        result = await get_moderation_history(page=1, page_size=20)
        assert result.total == 1
        assert result.entries[0].action == ModerationAction.VERIFY


# -- Frontend file test -------------------------------------------------------


class TestFrontend:
    def test_frontend_page_exists(self):
        import os

        assert os.path.exists("frontend/src/app/admin/moderacion/page.tsx")
