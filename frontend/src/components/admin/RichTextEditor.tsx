"use client";

import { useCallback, useEffect, useRef } from "react";
import {
  Bold,
  Italic,
  List,
  ListOrdered,
  Heading2,
  Undo,
  Redo,
  Minus,
} from "lucide-react";

// --- Spanish labels ---
const LABEL_BOLD = "Negrita";
const LABEL_ITALIC = "Cursiva";
const LABEL_UNORDERED_LIST = "Lista sin orden";
const LABEL_ORDERED_LIST = "Lista numerada";
const LABEL_HEADING = "Encabezado";
const LABEL_UNDO = "Deshacer";
const LABEL_REDO = "Rehacer";
const LABEL_SEPARATOR = "Linea separadora";
const LABEL_PLACEHOLDER = "Escriba las notas veterinarias aqui...";

interface RichTextEditorProps {
  value: string;
  onChange: (html: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  id?: string;
}

interface ToolbarButton {
  command: string;
  arg?: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
}

const TOOLBAR_BUTTONS: ToolbarButton[] = [
  { command: "bold", icon: Bold, label: LABEL_BOLD },
  { command: "italic", icon: Italic, label: LABEL_ITALIC },
  { command: "formatBlock", arg: "h3", icon: Heading2, label: LABEL_HEADING },
  { command: "insertUnorderedList", icon: List, label: LABEL_UNORDERED_LIST },
  { command: "insertOrderedList", icon: ListOrdered, label: LABEL_ORDERED_LIST },
  { command: "insertHorizontalRule", icon: Minus, label: LABEL_SEPARATOR },
];

/**
 * Minimal rich text editor using contenteditable with execCommand toolbar.
 * Stores content as an HTML string.
 */
export default function RichTextEditor({
  value,
  onChange,
  placeholder = LABEL_PLACEHOLDER,
  disabled = false,
  className = "",
  id,
}: RichTextEditorProps) {
  const editorRef = useRef<HTMLDivElement>(null);
  // Track whether the editor content change came from an internal edit
  const isInternalChange = useRef(false);

  // Sync external value into the editor when it changes from the outside
  useEffect(() => {
    if (!editorRef.current) return;
    // Only update if the change did not originate from the editor itself
    if (isInternalChange.current) {
      isInternalChange.current = false;
      return;
    }
    if (editorRef.current.innerHTML !== value) {
      editorRef.current.innerHTML = value;
    }
  }, [value]);

  const execFormat = useCallback(
    (command: string, arg?: string) => {
      if (disabled) return;
      // Ensure the editor has focus before executing
      editorRef.current?.focus();
      document.execCommand(command, false, arg);
      if (editorRef.current) {
        isInternalChange.current = true;
        onChange(editorRef.current.innerHTML);
      }
    },
    [disabled, onChange]
  );

  const handleInput = useCallback(() => {
    if (!editorRef.current) return;
    isInternalChange.current = true;
    onChange(editorRef.current.innerHTML);
  }, [onChange]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      // Bold: Ctrl+B / Cmd+B
      if ((e.ctrlKey || e.metaKey) && e.key === "b") {
        e.preventDefault();
        execFormat("bold");
      }
      // Italic: Ctrl+I / Cmd+I
      if ((e.ctrlKey || e.metaKey) && e.key === "i") {
        e.preventDefault();
        execFormat("italic");
      }
      // Undo: Ctrl+Z / Cmd+Z
      if ((e.ctrlKey || e.metaKey) && !e.shiftKey && e.key === "z") {
        e.preventDefault();
        execFormat("undo");
      }
      // Redo: Ctrl+Shift+Z / Cmd+Shift+Z
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === "z") {
        e.preventDefault();
        execFormat("redo");
      }
    },
    [execFormat]
  );

  const isEmpty = !value || value === "<br>" || value === "<div><br></div>";

  return (
    <div
      className={`rounded-lg border border-gray-300 focus-within:border-primary-500 focus-within:ring-1 focus-within:ring-primary-500 ${disabled ? "opacity-60" : ""} ${className}`}
    >
      {/* Toolbar */}
      <div
        className="flex flex-wrap items-center gap-0.5 border-b border-gray-200 bg-gray-50 px-2 py-1.5 rounded-t-lg"
        role="toolbar"
        aria-label="Herramientas de formato"
      >
        {TOOLBAR_BUTTONS.map((btn) => {
          const Icon = btn.icon;
          return (
            <button
              key={btn.command + (btn.arg ?? "")}
              type="button"
              onMouseDown={(e) => {
                // Prevent blur on the editor
                e.preventDefault();
                execFormat(btn.command, btn.arg);
              }}
              disabled={disabled}
              title={btn.label}
              aria-label={btn.label}
              className="rounded p-1.5 text-gray-600 hover:bg-gray-200 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40"
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
            </button>
          );
        })}

        <div className="mx-1 h-5 w-px bg-gray-300" role="separator" />

        {/* Undo/Redo */}
        <button
          type="button"
          onMouseDown={(e) => { e.preventDefault(); execFormat("undo"); }}
          disabled={disabled}
          title={LABEL_UNDO}
          aria-label={LABEL_UNDO}
          className="rounded p-1.5 text-gray-600 hover:bg-gray-200 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Undo className="h-4 w-4" aria-hidden="true" />
        </button>
        <button
          type="button"
          onMouseDown={(e) => { e.preventDefault(); execFormat("redo"); }}
          disabled={disabled}
          title={LABEL_REDO}
          aria-label={LABEL_REDO}
          className="rounded p-1.5 text-gray-600 hover:bg-gray-200 hover:text-gray-900 disabled:cursor-not-allowed disabled:opacity-40"
        >
          <Redo className="h-4 w-4" aria-hidden="true" />
        </button>
      </div>

      {/* Editable area */}
      <div className="relative">
        {isEmpty && (
          <p
            className="pointer-events-none absolute left-3 top-3 text-sm text-gray-400 select-none"
            aria-hidden="true"
          >
            {placeholder}
          </p>
        )}
        <div
          ref={editorRef}
          id={id}
          role="textbox"
          aria-multiline="true"
          aria-label="Editor de notas veterinarias"
          contentEditable={!disabled}
          suppressContentEditableWarning
          onInput={handleInput}
          onKeyDown={handleKeyDown}
          className={`min-h-[140px] px-3 py-3 text-sm text-gray-800 outline-none rounded-b-lg
            [&_strong]:font-bold [&_em]:italic
            [&_h3]:text-base [&_h3]:font-semibold [&_h3]:mt-2 [&_h3]:mb-1
            [&_ul]:list-disc [&_ul]:pl-5 [&_ul]:space-y-0.5
            [&_ol]:list-decimal [&_ol]:pl-5 [&_ol]:space-y-0.5
            [&_hr]:my-2 [&_hr]:border-gray-300
            ${disabled ? "cursor-not-allowed bg-gray-50" : "bg-white"}`}
        />
      </div>
    </div>
  );
}
