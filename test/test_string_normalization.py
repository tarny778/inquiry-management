import pytest
from pydantic import ValidationError

from schemas.schemas_auth import LoginRequest
from schemas.schemas_inquiries import InquiryCreate, InquiryUpdate, InquirySearch
from schemas.schemas_investigations import InvestigationUpdate
from schemas.string_normalization import blank_string_to_none


def inquiry_create_payload(**overrides):
    payload = {
        "問い合わせ職員番号": "T0001",
        "受付経路": "電話",
        "問い合わせ分類": "分類A",
        "件名": "テスト件名",
        "緊急度": 2,
        "受付時の処理": 2,
        "問い合わせ詳細": "問い合わせ内容",
        "受信日時": None,
    }
    payload.update(overrides)
    return payload


@pytest.mark.parametrize("blank", ["", "   ", "\t\n", "　"])
def test_required_inquiry_fields_reject_blank_strings(blank):
    for field in ("問い合わせ職員番号", "件名"):
        with pytest.raises(ValidationError):
            InquiryCreate(**inquiry_create_payload(**{field: blank}))


@pytest.mark.parametrize("blank", ["", "   ", "\t\n", "　", None])
def test_required_inquiry_fields_reject_blank_or_none(blank):
    for field in ("問い合わせ職員番号", "件名"):
        with pytest.raises(ValidationError):
            InquiryCreate(**inquiry_create_payload(**{field: blank}))
        with pytest.raises(ValidationError):
            InquiryUpdate(
                **inquiry_create_payload(
                    **{field: blank, "受信日時": "2026-10-28T10:00:00"}
                )
            )


@pytest.mark.parametrize("blank", ["", "   ", "\t\n", "　"])
def test_optional_inquiry_detail_normalizes_blank_to_none(blank):
    created = InquiryCreate(**inquiry_create_payload(問い合わせ詳細=blank))
    assert created.問い合わせ詳細 is None

    updated = InquiryUpdate(
        **inquiry_create_payload(問い合わせ詳細=blank, 受信日時="2026-10-28T10:00:00")
    )
    assert updated.問い合わせ詳細 is None


@pytest.mark.parametrize("blank", ["", "   ", "\t\n", "　"])
def test_inquiry_search_blank_strings_mean_no_filter(blank):
    search = InquirySearch(
        初期条件=2,
        問い合わせ職員番号=blank,
        問い合わせ当時の所属=blank,
        件名=blank,
        受付担当者=blank,
        対応担当者=blank,
    )
    for field in (
        "問い合わせ職員番号",
        "問い合わせ当時の所属",
        "件名",
        "受付担当者",
        "対応担当者",
    ):
        assert getattr(search, field) is None


@pytest.mark.parametrize("blank", ["", "   ", "\t\n", "　", None])
def test_investigation_update_rejects_blank_name(blank):
    with pytest.raises(ValidationError):
        InvestigationUpdate(**{"調査の名称": blank})


@pytest.mark.parametrize("field", ["原因・仮説", "情シス側での対応", "問い合わせ者側で必要な対応"])
@pytest.mark.parametrize("blank", ["", "   ", "\t\n", "　"])
def test_investigation_update_optional_text_normalizes_blank_to_none(field, blank):
    updated = InvestigationUpdate(**{field: blank})
    python_field = "原因仮説" if field == "原因・仮説" else field
    assert getattr(updated, python_field) is None


@pytest.mark.parametrize("field", ["職員番号", "パスワード"])
@pytest.mark.parametrize("blank", ["", "   ", "\t\n", "　"])
def test_login_rejects_blank_credentials(field, blank):
    payload = {"職員番号": "J0001", "パスワード": "Some-Password-123!"}
    payload[field] = blank
    with pytest.raises(ValidationError):
        LoginRequest(**payload)


def test_login_preserves_nonblank_password_whitespace():
    password = "  Valid-Password-123!  "
    request = LoginRequest(職員番号="J0001", パスワード=password)
    assert request.パスワード == password


@pytest.mark.parametrize("value", ["", "   ", "\t\n", "　"])
def test_blank_string_helper_returns_none(value):
    assert blank_string_to_none(value) is None


def test_blank_string_helper_preserves_nonblank_value():
    value = "  J0001  "
    assert blank_string_to_none(value) == value
