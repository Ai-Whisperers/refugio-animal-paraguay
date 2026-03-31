"""Unit tests for RAP-605: Expense management UI with receipts.

Tests cover:
- Admin expenses page structure
- Form fields and validation
- Receipt upload UX
- Expense list table
- Filtering controls
- Spanish labels and WCAG compliance
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


class TestAdminExpensesPage:
    """Tests for frontend/src/app/admin/expenses/page.tsx."""

    def setup_method(self) -> None:
        self.source = (FRONTEND_DIR / "src" / "app" / "admin" / "expenses" / "page.tsx").read_text()

    def test_file_exists(self) -> None:
        assert (FRONTEND_DIR / "src" / "app" / "admin" / "expenses" / "page.tsx").exists()

    def test_is_client_component(self) -> None:
        assert '"use client"' in self.source

    # -- Form fields --

    def test_amount_input(self) -> None:
        assert 'id="amount"' in self.source
        assert 'type="number"' in self.source

    def test_currency_selector(self) -> None:
        assert "PYG" in self.source
        assert "USD" in self.source
        assert "EUR" in self.source

    def test_category_dropdown(self) -> None:
        assert "Medico" in self.source
        assert "Alimento" in self.source
        assert "Refugio" in self.source
        assert "Rescate" in self.source
        assert "Operaciones" in self.source
        assert "Transporte" in self.source
        assert "Administracion" in self.source

    def test_description_textarea(self) -> None:
        assert "textarea" in self.source
        assert "Descripcion" in self.source

    def test_date_input(self) -> None:
        assert 'type="date"' in self.source
        assert "Fecha" in self.source

    def test_date_cannot_be_future(self) -> None:
        assert "La fecha no puede ser futura" in self.source

    # -- Receipt upload --

    def test_receipt_upload_button(self) -> None:
        assert "Cargar recibo" in self.source

    def test_receipt_accepts_images(self) -> None:
        assert 'accept="image/*"' in self.source

    def test_receipt_preview(self) -> None:
        assert "Vista previa del recibo" in self.source

    def test_uploading_state(self) -> None:
        assert "Subiendo..." in self.source

    def test_upload_error_message(self) -> None:
        assert "Error al cargar recibo" in self.source

    # -- Submit --

    def test_submit_button(self) -> None:
        assert "Guardar gasto" in self.source

    def test_success_message(self) -> None:
        assert "Gasto registrado" in self.source

    def test_submitting_state(self) -> None:
        assert "Guardando..." in self.source

    # -- Expense list --

    def test_table_role(self) -> None:
        assert 'role="table"' in self.source

    def test_table_columns(self) -> None:
        assert "Fecha" in self.source
        assert "Categoria" in self.source
        assert "Monto" in self.source
        assert "Descripcion" in self.source
        assert "Estado" in self.source

    def test_empty_state(self) -> None:
        assert "No hay gastos registrados" in self.source

    # -- Status badges --

    def test_status_pending(self) -> None:
        assert "Pendiente" in self.source
        assert "bg-yellow-100" in self.source

    def test_status_approved(self) -> None:
        assert "Aprobado" in self.source
        assert "bg-green-100" in self.source

    def test_status_rejected(self) -> None:
        assert "Rechazado" in self.source
        assert "bg-red-100" in self.source

    # -- Filters --

    def test_category_filter(self) -> None:
        assert "Todas las categorias" in self.source

    def test_status_filter(self) -> None:
        assert "Todos los estados" in self.source

    def test_date_range_filters(self) -> None:
        assert "Fecha desde" in self.source
        assert "Fecha hasta" in self.source

    # -- Accessibility --

    def test_form_labels(self) -> None:
        assert 'htmlFor="amount"' in self.source
        assert 'htmlFor="category"' in self.source
        assert 'htmlFor="description"' in self.source

    def test_aria_labels(self) -> None:
        assert 'aria-label="Moneda"' in self.source
        assert 'aria-label="Cargar recibo"' in self.source
        assert 'aria-label="Filtrar por categoria"' in self.source

    def test_aria_invalid(self) -> None:
        assert "aria-invalid" in self.source

    def test_wcag_touch_targets(self) -> None:
        assert "min-h-[44px]" in self.source

    def test_sr_only_file_input(self) -> None:
        assert "sr-only" in self.source

    # -- Page structure --

    def test_page_title(self) -> None:
        assert "Gestion de Gastos" in self.source

    def test_recent_expenses_heading(self) -> None:
        assert "Gastos Recientes" in self.source

    def test_add_expense_heading(self) -> None:
        assert "Agregar Gasto" in self.source

    # -- Validation --

    def test_required_field_validation(self) -> None:
        assert "Monto requerido" in self.source
        assert "Categoria requerida" in self.source
        assert "Descripcion requerida" in self.source
        assert "Fecha requerida" in self.source
