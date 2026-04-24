"use client";

import type { ReactNode } from "react";
import { useRef } from "react";
import { useFormStatus } from "react-dom";

type AutoSaveSettingsFormProps = {
  action: (formData: FormData) => void | Promise<void>;
  children: ReactNode;
};

function AutoSaveStatus() {
  const { pending } = useFormStatus();

  return (
    <div
      style={{
        display: "flex",
        justifyContent: "flex-end",
        color: "var(--muted)",
        fontSize: "0.95rem",
      }}
    >
      {pending ? "Сохраняем..." : "Сохраняется автоматически"}
    </div>
  );
}

export default function AutoSaveSettingsForm({ action, children }: AutoSaveSettingsFormProps) {
  const formRef = useRef<HTMLFormElement>(null);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  function submitForm() {
    formRef.current?.requestSubmit();
  }

  function handleChange(event: React.FormEvent<HTMLFormElement>) {
    const target = event.target;
    if (target instanceof HTMLSelectElement) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      submitForm();
    }
  }

  function handleBlur(event: React.FocusEvent<HTMLFormElement>) {
    const target = event.target;
    if (target instanceof HTMLInputElement) {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
        timeoutRef.current = null;
      }
      submitForm();
    }
  }

  return (
    <form ref={formRef} action={action} onChange={handleChange} onBlurCapture={handleBlur} style={{ display: "grid", gap: "18px" }}>
      {children}
      <AutoSaveStatus />
    </form>
  );
}
