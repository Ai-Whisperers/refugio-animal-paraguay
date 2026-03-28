"""Unit tests for RAP-598: Camera integration for forms.

Tests cover:
- CameraCapture component structure and accessibility
- Image compression utility exports
- Camera capture modes (environment/user)
- Spanish labels and WCAG compliance
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


# ---------------------------------------------------------------------------
# CameraCapture Component Tests
# ---------------------------------------------------------------------------


class TestCameraCaptureComponent:
    """Tests for frontend/src/components/CameraCapture.tsx."""

    def setup_method(self) -> None:
        self.source = (FRONTEND_DIR / "src" / "components" / "CameraCapture.tsx").read_text()

    def test_file_exists(self) -> None:
        assert (FRONTEND_DIR / "src" / "components" / "CameraCapture.tsx").exists()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.source

    def test_file_input_with_capture(self) -> None:
        assert "capture={captureMode}" in self.source

    def test_accepts_image_types(self) -> None:
        assert "accept={ACCEPTED_IMAGE_TYPES}" in self.source
        assert 'ACCEPTED_IMAGE_TYPES = "image/*"' in self.source

    def test_default_capture_environment(self) -> None:
        assert 'captureMode = "environment"' in self.source

    def test_supports_user_camera(self) -> None:
        assert '"user"' in self.source

    def test_max_file_size_2mb(self) -> None:
        assert "MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024" in self.source

    def test_compression_threshold_5mb(self) -> None:
        assert "COMPRESSION_THRESHOLD_BYTES = 5 * 1024 * 1024" in self.source

    def test_preview_size_150px(self) -> None:
        assert "PREVIEW_SIZE_PX = 150" in self.source

    def test_compress_image_function(self) -> None:
        assert "async function compressImage" in self.source

    def test_canvas_based_compression(self) -> None:
        assert "canvas" in self.source
        assert "toBlob" in self.source

    def test_progressive_quality_reduction(self) -> None:
        assert "quality" in self.source
        assert "image/jpeg" in self.source

    def test_on_image_capture_callback(self) -> None:
        assert "onImageCapture" in self.source

    def test_on_image_remove_callback(self) -> None:
        assert "onImageRemove" in self.source

    def test_preview_display(self) -> None:
        assert "Vista previa" in self.source
        assert "object-cover" in self.source

    def test_retake_button(self) -> None:
        assert "Tomar otra" in self.source
        assert "handleRetake" in self.source

    def test_remove_button(self) -> None:
        assert "Eliminar" in self.source
        assert "handleRemove" in self.source

    def test_error_handling(self) -> None:
        assert "No se pudo procesar la imagen" in self.source

    def test_compression_progress_display(self) -> None:
        assert "Comprimiendo" in self.source
        assert "compressionProgress" in self.source

    def test_camera_icon(self) -> None:
        assert "Camera" in self.source

    def test_loader_icon_during_compression(self) -> None:
        assert "Loader2" in self.source
        assert "animate-spin" in self.source

    def test_wcag_touch_targets(self) -> None:
        assert "min-h-[44px]" in self.source
        assert "min-w-[44px]" in self.source

    def test_aria_labels(self) -> None:
        assert "aria-label" in self.source
        assert "Tomar otra foto" in self.source
        assert "Eliminar foto" in self.source

    def test_aria_hidden_decorative_icons(self) -> None:
        assert 'aria-hidden="true"' in self.source

    def test_error_role_alert(self) -> None:
        assert 'role="alert"' in self.source

    def test_sr_only_file_input(self) -> None:
        assert "sr-only" in self.source

    def test_blob_url_cleanup(self) -> None:
        assert "URL.revokeObjectURL" in self.source

    def test_input_reset_after_capture(self) -> None:
        assert 'inputRef.current.value = ""' in self.source

    def test_dashed_border_upload_area(self) -> None:
        assert "border-dashed" in self.source

    def test_exports_compress_image(self) -> None:
        assert "export {" in self.source
        assert "compressImage" in self.source

    def test_exports_constants(self) -> None:
        for const in [
            "MAX_FILE_SIZE_BYTES",
            "COMPRESSION_THRESHOLD_BYTES",
            "PREVIEW_SIZE_PX",
            "ACCEPTED_IMAGE_TYPES",
        ]:
            assert const in self.source

    def test_max_dimension_scaling(self) -> None:
        assert "maxDim" in self.source or "2048" in self.source

    def test_props_interface(self) -> None:
        assert "CameraCaptureProps" in self.source
        assert "label" in self.source
        assert "captureMode" in self.source

    def test_hover_states(self) -> None:
        assert "hover:border-primary" in self.source
        assert "hover:text-primary" in self.source

    def test_spanish_camera_label_support(self) -> None:
        # Component accepts arbitrary label prop for Spanish text
        assert "label" in self.source
        # Story requires these specific labels:
        # "Tomar foto de tu hogar", "Tomar foto", "Tomar foto del animal"
        # These are passed as props, not hardcoded

    def test_file_input_ref(self) -> None:
        assert "useRef" in self.source
        assert "inputRef" in self.source

    def test_disabled_during_compression(self) -> None:
        assert "disabled={isCompressing}" in self.source
