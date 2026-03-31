"use client";

import { useEffect, useState, useCallback } from "react";
import {
  FileText,
  Download,
  Calendar,
  Clock,
  FileSpreadsheet,
  FileJson,
  PawPrint,
  Heart,
  DollarSign,
  Stethoscope,
  Users,
  BarChart3,
  AlertCircle,
  CheckCircle,
  Loader2,
} from "lucide-react";

// --- Constants ---
const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";

const REPORT_ICONS: Record<string, React.ElementType> = {
  animal_inventory: PawPrint,
  adoptions: Heart,
  donations: DollarSign,
  veterinary: Stethoscope,
  volunteers: Users,
  financial: BarChart3,
};

const REPORT_COLORS: Record<string, string> = {
  animal_inventory: "text-blue-600 bg-blue-50",
  adoptions: "text-red-600 bg-red-50",
  donations: "text-green-600 bg-green-50",
  veterinary: "text-purple-600 bg-purple-50",
  volunteers: "text-amber-600 bg-amber-50",
  financial: "text-teal-600 bg-teal-50",
};

// --- Types ---
interface ReportDefinition {
  report_type: string;
  title: string;
  description: string;
  columns: string[];
  available_formats: string[];
}

interface ReportRecord {
  id: string;
  report_type: string;
  title: string;
  export_format: string;
  status: string;
  row_count: number;
  file_size_bytes: number;
  generated_at: string;
}

// --- Components ---

function ReportCard({
  report,
  onGenerate,
  isGenerating,
}: {
  report: ReportDefinition;
  onGenerate: (type: string, format: string) => void;
  isGenerating: boolean;
}) {
  const Icon = REPORT_ICONS[report.report_type] ?? FileText;
  const colorClass = REPORT_COLORS[report.report_type] ?? "text-gray-600 bg-gray-50";

  return (
    <article
      className="border border-gray-200 rounded-xl p-5 bg-white hover:shadow-sm transition-shadow"
      aria-label={`Reporte: ${report.title}`}
    >
      <div className="flex items-start gap-4">
        <div className={`p-3 rounded-lg ${colorClass}`}>
          <Icon className="w-6 h-6" aria-hidden="true" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 mb-1">{report.title}</h3>
          <p className="text-sm text-gray-600 mb-3">{report.description}</p>
          <p className="text-xs text-gray-500 mb-4">
            Columnas: {report.columns.join(", ")}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => onGenerate(report.report_type, "csv")}
              disabled={isGenerating}
              className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg bg-primary-600 text-white hover:bg-primary-700 disabled:opacity-50 transition-colors min-h-[44px]"
              aria-label={`Exportar ${report.title} como CSV`}
            >
              {isGenerating ? (
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
              ) : (
                <FileSpreadsheet className="w-4 h-4" aria-hidden="true" />
              )}
              CSV
            </button>
            <button
              onClick={() => onGenerate(report.report_type, "json")}
              disabled={isGenerating}
              className="inline-flex items-center gap-2 px-4 py-2.5 text-sm font-medium rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 transition-colors min-h-[44px]"
              aria-label={`Exportar ${report.title} como JSON`}
            >
              {isGenerating ? (
                <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
              ) : (
                <FileJson className="w-4 h-4" aria-hidden="true" />
              )}
              JSON
            </button>
          </div>
        </div>
      </div>
    </article>
  );
}

function HistoryRow({ record }: { record: ReportRecord }) {
  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    return `${(bytes / 1024).toFixed(1)} KB`;
  };

  return (
    <tr className="border-b border-gray-100 hover:bg-gray-50">
      <td className="py-3 text-sm text-gray-900">{record.title}</td>
      <td className="py-3 text-sm text-gray-600 uppercase">{record.export_format}</td>
      <td className="py-3 text-sm text-gray-600">{record.row_count} filas</td>
      <td className="py-3 text-sm text-gray-600">{formatSize(record.file_size_bytes)}</td>
      <td className="py-3 text-sm text-gray-600">
        {new Date(record.generated_at).toLocaleString("es-PY")}
      </td>
      <td className="py-3">
        <span className="inline-flex items-center gap-1 text-xs font-medium text-green-700 bg-green-50 px-2 py-1 rounded-full">
          <CheckCircle className="w-3 h-3" aria-hidden="true" />
          {record.status === "completed" ? "Listo" : record.status}
        </span>
      </td>
      <td className="py-3">
        <a
          href={`${API_BASE}/api/admin/reports/${record.id}/download`}
          className="inline-flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 font-medium min-h-[44px] min-w-[44px] justify-center"
          aria-label={`Descargar ${record.title}`}
          download
        >
          <Download className="w-4 h-4" aria-hidden="true" />
        </a>
      </td>
    </tr>
  );
}

function LoadingSkeleton() {
  return (
    <div className="max-w-5xl mx-auto px-4 py-8" aria-busy="true" aria-label="Cargando reportes">
      <div className="h-8 bg-gray-200 rounded w-1/3 mb-6 animate-pulse" />
      <div className="grid gap-4 md:grid-cols-2">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="border rounded-xl p-5 animate-pulse">
            <div className="flex gap-4">
              <div className="w-12 h-12 bg-gray-200 rounded-lg" />
              <div className="flex-1">
                <div className="h-5 bg-gray-200 rounded w-2/3 mb-2" />
                <div className="h-4 bg-gray-200 rounded w-full mb-3" />
                <div className="h-10 bg-gray-200 rounded w-32" />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// --- Main Page ---
export default function ReportsPage() {
  const [reports, setReports] = useState<ReportDefinition[]>([]);
  const [history, setHistory] = useState<ReportRecord[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [generatingType, setGeneratingType] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      const [reportsRes, historyRes] = await Promise.all([
        fetch(`${API_BASE}/api/admin/reports/available`),
        fetch(`${API_BASE}/api/admin/reports/history`),
      ]);
      if (reportsRes.ok) setReports(await reportsRes.json());
      if (historyRes.ok) {
        const data = await historyRes.json();
        setHistory(data.reports ?? []);
      }
    } catch {
      setError("No se pudieron cargar los reportes disponibles.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleGenerate = async (reportType: string, format: string) => {
    setGeneratingType(reportType);
    setError(null);
    setSuccessMessage(null);
    try {
      const res = await fetch(`${API_BASE}/api/admin/reports/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          report_type: reportType,
          export_format: format,
        }),
      });
      if (!res.ok) throw new Error("Error al generar reporte");
      const data = await res.json();
      setHistory((prev) => [data, ...prev]);
      setSuccessMessage(`Reporte "${data.title}" generado exitosamente.`);

      // Auto-download
      const downloadUrl = `${API_BASE}/api/admin/reports/${data.id}/download`;
      window.open(downloadUrl, "_blank");
    } catch {
      setError("No se pudo generar el reporte. Intenta de nuevo.");
    } finally {
      setGeneratingType(null);
    }
  };

  if (isLoading) return <LoadingSkeleton />;

  return (
    <div className="max-w-5xl mx-auto px-4 py-6 sm:py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">
          Reportes exportables
        </h1>
        <p className="text-gray-600 mt-1">
          Genera y descarga reportes del refugio en formato CSV o JSON
        </p>
      </div>

      {/* Messages */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6 flex items-start gap-3" role="alert">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <p className="text-red-800 text-sm">{error}</p>
        </div>
      )}
      {successMessage && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6 flex items-start gap-3" role="status">
          <CheckCircle className="w-5 h-5 text-green-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
          <p className="text-green-800 text-sm">{successMessage}</p>
        </div>
      )}

      {/* Report Cards */}
      <div className="grid gap-4 md:grid-cols-2 mb-10">
        {reports.map((report) => (
          <ReportCard
            key={report.report_type}
            report={report}
            onGenerate={handleGenerate}
            isGenerating={generatingType === report.report_type}
          />
        ))}
      </div>

      {/* History */}
      {history.length > 0 && (
        <div>
          <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
            <Clock className="w-5 h-5 text-gray-500" aria-hidden="true" />
            Historial de reportes
          </h2>
          <div className="bg-white border border-gray-200 rounded-xl overflow-x-auto">
            <table className="w-full text-sm" aria-label="Historial de reportes generados">
              <thead>
                <tr className="border-b border-gray-200 bg-gray-50">
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">Reporte</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">Formato</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">Filas</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">Tamaño</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">Fecha</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">Estado</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-medium">Acción</th>
                </tr>
              </thead>
              <tbody>
                {history.map((record) => (
                  <HistoryRow key={record.id} record={record} />
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
