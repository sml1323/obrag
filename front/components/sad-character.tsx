"use client";

import { Character } from "./character";

interface SadCharacterProps {
  message?: string;
  size?: "sm" | "md" | "lg";
  daysStale?: number;
}

export function SadCharacter({
  message = "오래 방치됐어요...",
  size = "md",
  daysStale,
}: SadCharacterProps) {
  const displayMessage =
    daysStale !== undefined
      ? `${message} (${daysStale}일 동안 수정 없음)`
      : message;

  return (
    <Character mood="sad" size={size} message={displayMessage} showMessage={true} />
  );
}
