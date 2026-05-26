"use client";

import { useState, useCallback } from "react";
import type { ConfirmPayload, ConfirmHandle } from "@/types";

export function useConfirm(): ConfirmHandle {
  const [state, setState] = useState<{
    open: boolean;
    payload: ConfirmPayload | null;
  }>({ open: false, payload: null });

  const open = useCallback((payload: ConfirmPayload) => {
    setState({ open: true, payload });
  }, []);

  const close = useCallback(() => {
    setState((s) => ({ ...s, open: false }));
  }, []);

  return { open, close, props: { state, close } };
}
