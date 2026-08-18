import { useCallback, useState } from "react";

import { api, type ListQuery } from "@/lib/api-client";
import { useApi } from "@/lib/use-api";
import type { Page } from "@/lib/types";

interface UseListState<T> {
  data: Page<T> | null;
  loading: boolean;
  error: unknown;
  query: ListQuery;
  setSearch: (value: string) => void;
  setPage: (page: number, pageSize: number) => void;
  setSort: (sortBy: string, sortOrder?: "asc" | "desc") => void;
  setFilter: (key: string, value: string | undefined) => void;
  toggleSort: (key: string) => void;
  refetch: () => void;
  reset: () => void;
}

export function useList<T>(
  path: string,
  defaults: { pageSize?: number; sortBy?: string; sortOrder?: "asc" | "desc" } = {},
): UseListState<T> {
  const [query, setQuery] = useState<ListQuery>({
    page: 1,
    page_size: defaults.pageSize ?? 10,
    sort_by: defaults.sortBy,
    sort_order: defaults.sortOrder,
  });

  const { data, loading, error, refetch } = useApi<Page<T>>(path, query, [query]);

  const setSearch = useCallback((value: string) => {
    setQuery((q) => ({ ...q, page: 1, search: value || undefined }));
  }, []);

  const setPage = useCallback((page: number, pageSize: number) => {
    setQuery((q) => ({ ...q, page, page_size: pageSize }));
  }, []);

  const setSort = useCallback((sortBy: string, sortOrder?: "asc" | "desc") => {
    setQuery((q) => ({ ...q, sort_by: sortBy, sort_order: sortOrder ?? q.sort_order }));
  }, []);

  const toggleSort = useCallback((key: string) => {
    setQuery((q) => ({
      ...q,
      sort_by: key,
      sort_order: q.sort_by === key && q.sort_order === "asc" ? "desc" : "asc",
    }));
  }, []);

  const setFilter = useCallback((key: string, value: string | undefined) => {
    setQuery((q) => ({ ...q, page: 1, [key]: value || undefined }));
  }, []);

  const reset = useCallback(() => {
    setQuery({ page: 1, page_size: defaults.pageSize ?? 10 });
  }, [defaults.pageSize]);

  return { data, loading, error, query, setSearch, setPage, setSort, setFilter, toggleSort, refetch, reset };
}

export function useDelete(onDone: () => void, onError?: (message: string) => void) {
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const remove = useCallback(
    async (path: string) => {
      setDeletingId(path);
      setError(null);
      try {
        await api.delete(path);
        onDone();
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to delete";
        setError(message);
        onError?.(message);
      } finally {
        setDeletingId(null);
      }
    },
    [onDone, onError],
  );

  return { remove, deletingId, error };
}