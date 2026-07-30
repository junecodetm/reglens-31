"use client";

import { useId } from "react";

import type { DocumentExtraction } from "./reglens-types";

const CATEGORY_DISPLAY_ORDER = [
  "Title 31 — Code of Federal Regulations parts",
  "Sanctions notices & general licenses (OFAC)",
  "IRS & tax regulations",
  "Other Treasury & joint-agency rules",
] as const;

interface DocumentPickerProps {
  documents: DocumentExtraction[];
  selectedDocumentNumber: string;
  onSelect: (documentNumber: string) => void;
}

export function formatDocumentOptionLabel(
  document: Pick<DocumentExtraction, "document_title">,
): string {
  return document.document_title.replace(
    /\(point-in-time (\d{4}-\d{2}-\d{2})\)/,
    "($1)",
  );
}

export function groupDocumentsByCategory(
  documents: DocumentExtraction[],
): Array<{ category: string; documents: DocumentExtraction[] }> {
  const documentsByCategory = new Map<string, DocumentExtraction[]>();

  for (const document of documents) {
    const categoryDocuments =
      documentsByCategory.get(document.category) ?? [];

    categoryDocuments.push(document);
    documentsByCategory.set(document.category, categoryDocuments);
  }

  const displayIndex = new Map<string, number>(
    CATEGORY_DISPLAY_ORDER.map((category, index) => [category, index]),
  );

  return Array.from(documentsByCategory, ([category, categoryDocuments]) => ({
    category,
    documents: [...categoryDocuments].sort((left, right) =>
      left.document_number.localeCompare(right.document_number),
    ),
  })).sort((left, right) => {
    const leftIndex = displayIndex.get(left.category);
    const rightIndex = displayIndex.get(right.category);

    if (leftIndex !== undefined && rightIndex !== undefined) {
      return leftIndex - rightIndex;
    }

    if (leftIndex !== undefined) {
      return -1;
    }

    if (rightIndex !== undefined) {
      return 1;
    }

    return left.category.localeCompare(right.category);
  });
}

export function DocumentPicker({
  documents,
  selectedDocumentNumber,
  onSelect,
}: DocumentPickerProps) {
  const selectId = useId();
  const groups = groupDocumentsByCategory(documents);

  return (
    <div className="document-picker">
      <label className="usa-label" htmlFor={selectId}>
        Document
      </label>
      <select
        className="usa-select"
        id={selectId}
        value={selectedDocumentNumber}
        onChange={(event) => onSelect(event.target.value)}
      >
        {groups.map((group) => {
          const normalizedLabelCounts = new Map<string, number>();

          for (const document of group.documents) {
            const optionLabel = formatDocumentOptionLabel(document);
            normalizedLabelCounts.set(
              optionLabel,
              (normalizedLabelCounts.get(optionLabel) ?? 0) + 1,
            );
          }

          return (
            <optgroup label={group.category} key={group.category}>
              {group.documents.map((document) => {
                const optionLabel = formatDocumentOptionLabel(document);
                const visibleOptionLabel =
                  normalizedLabelCounts.get(optionLabel) === 1
                    ? optionLabel
                    : `${optionLabel} — ${document.document_number}`;

                return (
                  <option
                    value={document.document_number}
                    key={document.document_number}
                  >
                    {visibleOptionLabel}
                  </option>
                );
              })}
            </optgroup>
          );
        })}
      </select>
    </div>
  );
}
