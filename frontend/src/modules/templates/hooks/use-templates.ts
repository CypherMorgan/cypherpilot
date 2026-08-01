/** TanStack Query hooks for Templates. */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createTemplate,
  deleteTemplate,
  listTemplates,
  updateTemplate,
} from "@/modules/templates/services/templates";
import type {
  CreateTemplatePayload,
  UpdateTemplatePayload,
} from "@/modules/templates/types";

const TEMPLATE_KEYS = {
  all: ["templates"] as const,
  list: (page?: number) => [...TEMPLATE_KEYS.all, "list", page] as const,
};

/**
 * Fetch the current user's templates (first page).
 */
export function useTemplates(page: number = 1) {
  return useQuery({
    queryKey: TEMPLATE_KEYS.list(page),
    queryFn: () => listTemplates({ page }),
    staleTime: 30_000,
  });
}

/**
 * Create a template, then invalidate the list cache.
 */
export function useCreateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: CreateTemplatePayload) => createTemplate(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
    },
  });
}

/**
 * Update a template, then invalidate the list cache.
 */
export function useUpdateTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      templateId,
      data,
    }: {
      templateId: string;
      data: UpdateTemplatePayload;
    }) => updateTemplate(templateId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
    },
  });
}

/**
 * Delete a template, then invalidate the list cache.
 */
export function useDeleteTemplate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (templateId: string) => deleteTemplate(templateId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: TEMPLATE_KEYS.all });
    },
  });
}
