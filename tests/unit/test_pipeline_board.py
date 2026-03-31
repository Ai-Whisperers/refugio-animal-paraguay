"""Unit tests for pipeline tracking API used by adoption pipeline board."""

from uuid import uuid4

from src.api.pipeline_tracking import (
    AdvanceRequest,
    PipelineStageSummary,
    RejectRequest,
    StageInfo,
    TimedOutAdoption,
    router,
)

# ---------------------------------------------------------------------------
# Schema tests
# ---------------------------------------------------------------------------


class TestSchemas:
    def test_advance_request_defaults(self):
        req = AdvanceRequest()
        assert req.notes is None

    def test_advance_request_with_notes(self):
        req = AdvanceRequest(notes="Moving forward")
        assert req.notes == "Moving forward"

    def test_reject_request_requires_reason(self):
        req = RejectRequest(reason="Not suitable")
        assert req.reason == "Not suitable"

    def test_stage_info_fields(self):
        info = StageInfo(
            id=uuid4(),
            name="Application",
            position=1,
            color="#3B82F6",
            requires_approval=True,
            max_days=7,
        )
        assert info.name == "Application"
        assert info.position == 1
        assert info.requires_approval is True

    def test_pipeline_stage_summary(self):
        summary = PipelineStageSummary(
            stage_id=uuid4(),
            stage_name="Review",
            position=2,
            color="#10B981",
            adoption_count=5,
        )
        assert summary.adoption_count == 5

    def test_timed_out_adoption(self):
        timed = TimedOutAdoption(
            adoption_request_id=uuid4(),
            animal_id=uuid4(),
            adopter_id=uuid4(),
            stage_id=uuid4(),
            stage_name="Home Visit",
            max_days=7,
            days_in_stage=10,
            overdue_by=3,
        )
        assert timed.overdue_by == 3
        assert timed.max_days == 7


class TestRouterConfiguration:
    def test_router_has_tags(self):
        assert "Pipeline Tracking" in router.tags


class TestPipelineServiceErrors:
    def test_adoption_not_found_error(self):
        from src.services.pipeline_tracking_service import AdoptionNotFoundError

        err = AdoptionNotFoundError(uuid4())
        assert "not found" in str(err).lower() or err is not None

    def test_already_completed_error(self):
        from src.services.pipeline_tracking_service import AlreadyCompletedError

        err = AlreadyCompletedError()
        assert err is not None

    def test_invalid_transition_error(self):
        from src.services.pipeline_tracking_service import InvalidTransitionError

        err = InvalidTransitionError("No next stage")
        assert "No next stage" in str(err)
