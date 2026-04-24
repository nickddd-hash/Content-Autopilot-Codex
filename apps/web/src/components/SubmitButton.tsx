"use client";

import type { CSSProperties, ReactNode } from "react";
import { useFormStatus } from "react-dom";

type SubmitButtonProps = {
  children: ReactNode;
  pendingLabel?: string;
  className?: string;
  style?: CSSProperties;
};

function Spinner() {
  return (
    <span
      aria-hidden="true"
      style={{
        width: "14px",
        height: "14px",
        borderRadius: "999px",
        border: "2px solid currentColor",
        borderRightColor: "transparent",
        display: "inline-block",
        animation: "button-spin 0.8s linear infinite",
      }}
    />
  );
}

export default function SubmitButton({
  children,
  pendingLabel = "Сохраняем...",
  className,
  style,
}: SubmitButtonProps) {
  const { pending } = useFormStatus();

  return (
    <>
      <button
        type="submit"
        className={className}
        style={{
          ...style,
          opacity: pending ? 0.8 : undefined,
          pointerEvents: pending ? "none" : undefined,
          display: "inline-flex",
          alignItems: "center",
          gap: "10px",
        }}
        disabled={pending}
      >
        {pending ? <Spinner /> : null}
        <span>{pending ? pendingLabel : children}</span>
      </button>
      <style jsx>{`
        @keyframes button-spin {
          from {
            transform: rotate(0deg);
          }
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </>
  );
}
