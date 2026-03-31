"""Exportable reports API (PDF/CSV).

Generates downloadable reports from shelter analytics data in CSV and
JSON formats. Supports animal inventory, adoption, donation, veterinary,
and volunteer reports.

Endpoints:
    GET  /api/admin/reports/available             -- list available reports
    POST /api/admin/reports/generate              -- generate a report
    GET  /api/admin/reports/history                -- report generation history
    GET  /api/admin/reports/{report_id}/download   -- download generated report
"""

import csv
import io
import json
import logging
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/admin/reports",
    tags=["report-export"],
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_REPORT_ROWS = 10_000
REPORT_RETENTION_DAYS = 30
CSV_DELIMITER = ","
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class ReportType(StrEnum):
    """Available report types."""

    ANIMAL_INVENTORY = "animal_inventory"
    ADOPTIONS = "adoptions"
    DONATIONS = "donations"
    VETERINARY = "veterinary"
    VOLUNTEERS = "volunteers"
    FINANCIAL = "financial"


class ExportFormat(StrEnum):
    """Supported export formats."""

    CSV = "csv"
    JSON = "json"


class ReportStatus(StrEnum):
    """Report generation status."""

    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


REPORT_DEFINITIONS: dict[str, dict[str, Any]] = {
    "animal_inventory": {
        "title": "Inventario de animales",
        "description": "Lista completa de animales en el refugio con estado actual",
        "columns": [
            "id",
            "nombre",
            "especie",
            "raza",
            "edad",
            "sexo",
            "estado",
            "fecha_ingreso",
            "ubicacion",
        ],
    },
    "adoptions": {
        "title": "Reporte de adopciones",
        "description": "Historial de adopciones completadas y en proceso",
        "columns": [
            "id",
            "animal",
            "adoptante",
            "fecha_solicitud",
            "fecha_aprobacion",
            "estado",
            "seguimiento",
        ],
    },
    "donations": {
        "title": "Reporte de donaciones",
        "description": "Historial de donaciones recibidas con detalle de donante",
        "columns": [
            "id",
            "donante",
            "monto",
            "moneda",
            "fecha",
            "metodo_pago",
            "campana",
            "estado",
        ],
    },
    "veterinary": {
        "title": "Reporte veterinario",
        "description": "Tratamientos, vacunaciones y procedimientos realizados",
        "columns": [
            "id",
            "animal",
            "tipo_tratamiento",
            "descripcion",
            "veterinario",
            "fecha",
            "costo",
            "estado",
        ],
    },
    "volunteers": {
        "title": "Reporte de voluntarios",
        "description": "Registro de voluntarios y horas de servicio",
        "columns": [
            "id",
            "nombre",
            "email",
            "telefono",
            "horas_totales",
            "ultima_actividad",
            "estado",
        ],
    },
    "financial": {
        "title": "Reporte financiero",
        "description": "Resumen de ingresos y gastos del refugio",
        "columns": [
            "periodo",
            "ingresos_donaciones",
            "ingresos_adopciones",
            "gastos_veterinarios",
            "gastos_alimentacion",
            "gastos_operativos",
            "balance",
        ],
    },
}


# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class ReportDefinition(BaseModel):
    """Available report definition."""

    report_type: ReportType
    title: str
    description: str
    columns: list[str]
    available_formats: list[ExportFormat] = [ExportFormat.CSV, ExportFormat.JSON]


class ReportGenerateRequest(BaseModel):
    """Request to generate a report."""

    report_type: ReportType
    export_format: ExportFormat = ExportFormat.CSV
    date_from: str | None = Field(default=None, max_length=10)
    date_to: str | None = Field(default=None, max_length=10)
    filters: dict[str, str] = Field(default_factory=dict)


class ReportRecord(BaseModel):
    """Generated report record."""

    id: str
    report_type: ReportType
    title: str
    export_format: ExportFormat
    status: ReportStatus
    row_count: int
    file_size_bytes: int
    generated_at: str
    date_from: str | None = None
    date_to: str | None = None


class ReportHistoryResponse(BaseModel):
    """Report generation history."""

    reports: list[ReportRecord]
    total: int


# ---------------------------------------------------------------------------
# In-memory store and sample data generators
# ---------------------------------------------------------------------------

_generated_reports: dict[str, dict[str, Any]] = {}


def _reset_store() -> None:
    """Reset in-memory store (for testing)."""
    _generated_reports.clear()


def _generate_sample_data(report_type: str, max_rows: int = 20) -> list[dict[str, str]]:
    """Generate sample data for a report type."""
    columns = REPORT_DEFINITIONS[report_type]["columns"]
    rows: list[dict[str, str]] = []

    if report_type == "animal_inventory":
        animals = [
            ("Luna", "Perro", "Mestizo", "3 años", "Hembra", "Disponible"),
            ("Max", "Perro", "Labrador", "5 años", "Macho", "Adoptado"),
            ("Michi", "Gato", "Siamés", "2 años", "Hembra", "Disponible"),
            ("Rocky", "Perro", "Pastor", "4 años", "Macho", "En tratamiento"),
            ("Nala", "Gato", "Persa", "1 año", "Hembra", "Disponible"),
            ("Thor", "Perro", "Pitbull", "6 años", "Macho", "En adopción"),
            ("Cleo", "Gato", "Mestizo", "3 años", "Hembra", "Adoptado"),
            ("Simba", "Gato", "Naranja", "2 años", "Macho", "Disponible"),
        ]
        for i, (nombre, especie, raza, edad, sexo, estado_animal) in enumerate(animals[:max_rows]):
            rows.append(
                {
                    "id": str(i + 1),
                    "nombre": nombre,
                    "especie": especie,
                    "raza": raza,
                    "edad": edad,
                    "sexo": sexo,
                    "estado": estado_animal,
                    "fecha_ingreso": f"2026-0{(i % 3) + 1}-{(i * 3 + 5) % 28 + 1:02d}",
                    "ubicacion": f"Sector {chr(65 + i % 4)}",
                }
            )
    elif report_type == "donations":
        donors = [
            ("Maria García", "500000", "PYG", "Transferencia", "General"),
            ("Hans Mueller", "100", "EUR", "SEPA", "Esterilización"),
            ("Juan Pérez", "200000", "PYG", "Tigo Money", "Alimentación"),
            ("Anna Schmidt", "50", "EUR", "Tarjeta", "General"),
            ("Pedro López", "150000", "PYG", "Transferencia", "Veterinario"),
        ]
        for i, (donante, monto, moneda, metodo, campana) in enumerate(donors[:max_rows]):
            rows.append(
                {
                    "id": str(i + 1),
                    "donante": donante,
                    "monto": monto,
                    "moneda": moneda,
                    "fecha": f"2026-03-{(i * 5 + 1) % 28 + 1:02d}",
                    "metodo_pago": metodo,
                    "campana": campana,
                    "estado": "Completado",
                }
            )
    else:
        for i in range(min(5, max_rows)):
            row = {col: f"Dato-{i + 1}" for col in columns}
            row["id"] = str(i + 1)
            rows.append(row)

    return rows


def _data_to_csv(columns: list[str], rows: list[dict[str, str]]) -> str:
    """Convert data to CSV string."""
    output = io.StringIO()
    writer = csv.DictWriter(
        output, fieldnames=columns, delimiter=CSV_DELIMITER, extrasaction="ignore"
    )
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def _data_to_json(rows: list[dict[str, str]]) -> str:
    """Convert data to JSON string."""
    return json.dumps(rows, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/available", response_model=list[ReportDefinition])
async def list_available_reports() -> list[ReportDefinition]:
    """List all available report types."""
    return [
        ReportDefinition(
            report_type=ReportType(key),
            title=defn["title"],
            description=defn["description"],
            columns=defn["columns"],
        )
        for key, defn in REPORT_DEFINITIONS.items()
    ]


@router.post("/generate", response_model=ReportRecord, status_code=status.HTTP_201_CREATED)
async def generate_report(request: ReportGenerateRequest) -> ReportRecord:
    """Generate a report and store it for download."""
    if request.report_type not in REPORT_DEFINITIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown report type: {request.report_type}",
        )

    defn = REPORT_DEFINITIONS[request.report_type]
    rows = _generate_sample_data(request.report_type)

    if request.export_format == ExportFormat.CSV:
        content = _data_to_csv(defn["columns"], rows)
        content_type = "text/csv"
    else:
        content = _data_to_json(rows)
        content_type = "application/json"

    now = datetime.now(UTC).isoformat()
    report_id = str(uuid4())

    record: dict[str, Any] = {
        "id": report_id,
        "report_type": request.report_type,
        "title": defn["title"],
        "export_format": request.export_format,
        "status": ReportStatus.COMPLETED,
        "row_count": len(rows),
        "file_size_bytes": len(content.encode("utf-8")),
        "generated_at": now,
        "date_from": request.date_from,
        "date_to": request.date_to,
        "content": content,
        "content_type": content_type,
    }
    _generated_reports[report_id] = record

    logger.info(
        "Report generated",
        extra={
            "report_id": report_id,
            "type": request.report_type,
            "format": request.export_format,
            "rows": len(rows),
        },
    )

    return ReportRecord(
        id=report_id,
        report_type=request.report_type,
        title=defn["title"],
        export_format=request.export_format,
        status=ReportStatus.COMPLETED,
        row_count=len(rows),
        file_size_bytes=len(content.encode("utf-8")),
        generated_at=now,
        date_from=request.date_from,
        date_to=request.date_to,
    )


@router.get("/history", response_model=ReportHistoryResponse)
async def get_report_history(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> ReportHistoryResponse:
    """Get report generation history."""
    records = sorted(
        _generated_reports.values(),
        key=lambda r: r["generated_at"],
        reverse=True,
    )
    total = len(records)
    start = (page - 1) * page_size
    page_records = records[start : start + page_size]

    return ReportHistoryResponse(
        reports=[
            ReportRecord(
                id=r["id"],
                report_type=r["report_type"],
                title=r["title"],
                export_format=r["export_format"],
                status=r["status"],
                row_count=r["row_count"],
                file_size_bytes=r["file_size_bytes"],
                generated_at=r["generated_at"],
                date_from=r.get("date_from"),
                date_to=r.get("date_to"),
            )
            for r in page_records
        ],
        total=total,
    )


@router.get("/{report_id}/download")
async def download_report(report_id: str) -> StreamingResponse:
    """Download a generated report."""
    record = _generated_reports.get(report_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report '{report_id}' not found",
        )

    content = record["content"]
    content_type = record["content_type"]
    ext = "csv" if record["export_format"] == ExportFormat.CSV else "json"
    filename = f"{record['report_type']}_{record['generated_at'][:10]}.{ext}"

    return StreamingResponse(
        iter([content]),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
