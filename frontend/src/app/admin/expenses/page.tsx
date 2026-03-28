"use client";

import { useState, useCallback } from "react";
import {
  Plus,
  Filter,
  Receipt,
  CheckCircle,
  XCircle,
  Clock,
  Upload,
  Loader2,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const CATEGORIES = [
  { value: "medical", label: "Medico" },
  { value: "food", label: "Alimento" },
  { value: "shelter", label: "Refugio" },
  { value: "rescue", label: "Rescate" },
  { value: "operations", label: "Operaciones" },
  { value: "transport", label: "Transporte" },
  { value: "admin", label: "Administracion" },
  { value: "other", label: "Otro" },
];

const CURRENCIES = ["PYG", "USD", "EUR"];

const STATUS_STYLES: Record<string, { bg: string; text: string; label: string }> = {
  pending: { bg: "bg-yellow-100", text: "text-yellow-800", label: "Pendiente" },
  approved: { bg: "bg-green-100", text: "text-green-800", label: "Aprobado" },
  rejected: { bg: "bg-red-100", text: "text-red-800", label: "Rechazado" },
};

const PAGE_SIZE = 20;

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface Expense {
  id: string;
  amount_cents: number;
  currency: string;
  category: string;
  description: string;
  expense_date: string;
  status: string;
  receipt_url: string | null;
}

// ---------------------------------------------------------------------------
// Status Badge
// ---------------------------------------------------------------------------

function StatusBadge({ status }: { status: string }) {
  const style = STATUS_STYLES[status] ?? STATUS_STYLES.pending;
  return (
    <span
      className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${style.bg} ${style.text}`}
    >
      {status === "approved" && <CheckCircle className="w-3 h-3" aria-hidden="true" />}
      {status === "rejected" && <XCircle className="w-3 h-3" aria-hidden="true" />}
      {status === "pending" && <Clock className="w-3 h-3" aria-hidden="true" />}
      {style.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Category Badge
// ---------------------------------------------------------------------------

function CategoryBadge({ category }: { category: string }) {
  const cat = CATEGORIES.find((c) => c.value === category);
  return (
    <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-gray-100 text-gray-700">
      {cat?.label ?? category}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Add Expense Form
// ---------------------------------------------------------------------------

function AddExpenseForm({
  onSubmit,
}: {
  onSubmit: (data: {
    amount_cents: number;
    currency: string;
    category: string;
    description: string;
    expense_date: string;
  }) => Promise<boolean>;
}) {
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("PYG");
  const [category, setCategory] = useState("");
  const [description, setDescription] = useState("");
  const [expenseDate, setExpenseDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [receiptPreview, setReceiptPreview] = useState<string | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = useCallback((): boolean => {
    const newErrors: Record<string, string> = {};
    if (!amount || Number(amount) <= 0) newErrors.amount = "Monto requerido";
    if (!category) newErrors.category = "Categoria requerida";
    if (!description.trim()) newErrors.description = "Descripcion requerida";
    if (!expenseDate) newErrors.expense_date = "Fecha requerida";
    if (expenseDate > new Date().toISOString().split("T")[0]) {
      newErrors.expense_date = "La fecha no puede ser futura";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }, [amount, category, description, expenseDate]);

  const handleReceiptChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      setIsUploading(true);
      setUploadError(null);

      // Simulate upload — in production would POST to storage
      const reader = new FileReader();
      reader.onload = () => {
        setReceiptPreview(reader.result as string);
        setIsUploading(false);
      };
      reader.onerror = () => {
        setUploadError("Error al cargar recibo");
        setIsUploading(false);
      };
      reader.readAsDataURL(file);
    },
    []
  );

  const handleSubmit = useCallback(
    async (e: React.FormEvent) => {
      e.preventDefault();
      if (!validate()) return;

      setIsSubmitting(true);
      const success = await onSubmit({
        amount_cents: Math.round(Number(amount) * 100),
        currency,
        category,
        description: description.trim(),
        expense_date: expenseDate,
      });

      if (success) {
        setSuccessMessage("Gasto registrado");
        setAmount("");
        setCategory("");
        setDescription("");
        setReceiptPreview(null);
        setTimeout(() => setSuccessMessage(null), 3000);
      }
      setIsSubmitting(false);
    },
    [amount, currency, category, description, expenseDate, validate, onSubmit]
  );

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-lg border p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
        <Plus className="w-5 h-5" aria-hidden="true" />
        Agregar Gasto
      </h2>

      {successMessage && (
        <div
          role="status"
          className="mb-4 p-3 bg-green-50 text-green-800 rounded-md text-sm flex items-center gap-2"
        >
          <CheckCircle className="w-4 h-4" aria-hidden="true" />
          {successMessage}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Amount + Currency */}
        <div>
          <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-1">
            Monto *
          </label>
          <div className="flex gap-2">
            <input
              id="amount"
              type="number"
              min="0"
              step="0.01"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-invalid={!!errors.amount}
            />
            <select
              value={currency}
              onChange={(e) => setCurrency(e.target.value)}
              className="rounded-md border border-gray-300 px-3 py-2 text-sm"
              aria-label="Moneda"
            >
              {CURRENCIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          {errors.amount && (
            <p className="mt-1 text-xs text-red-600">{errors.amount}</p>
          )}
        </div>

        {/* Category */}
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-1">
            Categoria *
          </label>
          <select
            id="category"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            aria-invalid={!!errors.category}
          >
            <option value="">Seleccionar...</option>
            {CATEGORIES.map((c) => (
              <option key={c.value} value={c.value}>
                {c.label}
              </option>
            ))}
          </select>
          {errors.category && (
            <p className="mt-1 text-xs text-red-600">{errors.category}</p>
          )}
        </div>

        {/* Description */}
        <div className="sm:col-span-2">
          <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
            Descripcion *
          </label>
          <textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            aria-invalid={!!errors.description}
          />
          {errors.description && (
            <p className="mt-1 text-xs text-red-600">{errors.description}</p>
          )}
        </div>

        {/* Date */}
        <div>
          <label htmlFor="expense-date" className="block text-sm font-medium text-gray-700 mb-1">
            Fecha *
          </label>
          <input
            id="expense-date"
            type="date"
            value={expenseDate}
            max={new Date().toISOString().split("T")[0]}
            onChange={(e) => setExpenseDate(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            aria-invalid={!!errors.expense_date}
          />
          {errors.expense_date && (
            <p className="mt-1 text-xs text-red-600">{errors.expense_date}</p>
          )}
        </div>

        {/* Receipt Upload */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Recibo
          </label>
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2 px-3 py-2 border border-gray-300 rounded-md cursor-pointer hover:bg-gray-50 text-sm min-h-[44px]">
              {isUploading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" aria-hidden="true" />
                  Subiendo...
                </>
              ) : (
                <>
                  <Upload className="w-4 h-4" aria-hidden="true" />
                  Cargar recibo
                </>
              )}
              <input
                type="file"
                accept="image/*"
                onChange={handleReceiptChange}
                className="sr-only"
                aria-label="Cargar recibo"
              />
            </label>
            {receiptPreview && (
              <div className="w-12 h-12 rounded border overflow-hidden flex-shrink-0">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={receiptPreview}
                  alt="Vista previa del recibo"
                  className="w-full h-full object-cover"
                />
              </div>
            )}
          </div>
          {uploadError && (
            <p className="mt-1 text-xs text-red-600">{uploadError}</p>
          )}
        </div>
      </div>

      {/* Submit */}
      <div className="mt-6">
        <button
          type="submit"
          disabled={isSubmitting}
          className="px-6 py-2 bg-primary-600 text-white rounded-md hover:bg-primary-700 disabled:opacity-50 text-sm font-medium min-h-[44px]"
        >
          {isSubmitting ? "Guardando..." : "Guardar gasto"}
        </button>
      </div>
    </form>
  );
}

// ---------------------------------------------------------------------------
// Expense List Table
// ---------------------------------------------------------------------------

function ExpenseListTable({ expenses }: { expenses: Expense[] }) {
  if (expenses.length === 0) {
    return (
      <div className="text-center py-12 text-gray-500">
        <Receipt className="w-12 h-12 mx-auto mb-3 opacity-40" aria-hidden="true" />
        <p>No hay gastos registrados</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm" role="table">
        <thead>
          <tr className="border-b text-left text-gray-500">
            <th className="py-3 px-4 font-medium">Fecha</th>
            <th className="py-3 px-4 font-medium">Categoria</th>
            <th className="py-3 px-4 font-medium text-right">Monto</th>
            <th className="py-3 px-4 font-medium">Descripcion</th>
            <th className="py-3 px-4 font-medium">Estado</th>
          </tr>
        </thead>
        <tbody>
          {expenses.map((expense) => (
            <tr key={expense.id} className="border-b hover:bg-gray-50">
              <td className="py-3 px-4 whitespace-nowrap">{expense.expense_date}</td>
              <td className="py-3 px-4">
                <CategoryBadge category={expense.category} />
              </td>
              <td className="py-3 px-4 text-right whitespace-nowrap font-medium">
                {(expense.amount_cents / 100).toLocaleString()} {expense.currency}
              </td>
              <td className="py-3 px-4 max-w-xs truncate">{expense.description}</td>
              <td className="py-3 px-4">
                <StatusBadge status={expense.status} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Filters
// ---------------------------------------------------------------------------

function ExpenseFilters({
  onFilterChange,
}: {
  onFilterChange: (filters: {
    category: string;
    status: string;
    dateFrom: string;
    dateTo: string;
  }) => void;
}) {
  const [category, setCategory] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");

  const handleChange = useCallback(() => {
    onFilterChange({
      category,
      status: filterStatus,
      dateFrom,
      dateTo,
    });
  }, [category, filterStatus, dateFrom, dateTo, onFilterChange]);

  return (
    <div className="flex flex-wrap items-center gap-3 p-4 bg-gray-50 rounded-lg">
      <Filter className="w-4 h-4 text-gray-500" aria-hidden="true" />
      <select
        value={category}
        onChange={(e) => {
          setCategory(e.target.value);
          handleChange();
        }}
        className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        aria-label="Filtrar por categoria"
      >
        <option value="">Todas las categorias</option>
        {CATEGORIES.map((c) => (
          <option key={c.value} value={c.value}>
            {c.label}
          </option>
        ))}
      </select>
      <select
        value={filterStatus}
        onChange={(e) => {
          setFilterStatus(e.target.value);
          handleChange();
        }}
        className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        aria-label="Filtrar por estado"
      >
        <option value="">Todos los estados</option>
        <option value="pending">Pendiente</option>
        <option value="approved">Aprobado</option>
        <option value="rejected">Rechazado</option>
      </select>
      <input
        type="date"
        value={dateFrom}
        onChange={(e) => {
          setDateFrom(e.target.value);
          handleChange();
        }}
        className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        aria-label="Fecha desde"
      />
      <input
        type="date"
        value={dateTo}
        onChange={(e) => {
          setDateTo(e.target.value);
          handleChange();
        }}
        className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        aria-label="Fecha hasta"
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main Page
// ---------------------------------------------------------------------------

export default function AdminExpensesPage() {
  const [expenses] = useState<Expense[]>([]);

  const handleSubmit = useCallback(
    async (_data: {
      amount_cents: number;
      currency: string;
      category: string;
      description: string;
      expense_date: string;
    }) => {
      // MVP: would POST to /api/admin/expenses
      return true;
    },
    []
  );

  const handleFilterChange = useCallback(
    (_filters: {
      category: string;
      status: string;
      dateFrom: string;
      dateTo: string;
    }) => {
      // MVP: would refetch with filters
    },
    []
  );

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
        <Receipt className="w-6 h-6" aria-hidden="true" />
        Gestion de Gastos
      </h1>

      {/* Add expense form */}
      <div className="mb-8">
        <AddExpenseForm onSubmit={handleSubmit} />
      </div>

      {/* Filters */}
      <div className="mb-4">
        <ExpenseFilters onFilterChange={handleFilterChange} />
      </div>

      {/* Expense list */}
      <div className="bg-white rounded-lg border">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">
            Gastos Recientes
          </h2>
        </div>
        <ExpenseListTable expenses={expenses} />
      </div>
    </div>
  );
}
