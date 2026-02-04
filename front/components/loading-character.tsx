"use client";

import { Character, type CharacterMood } from "./character";

interface LoadingCharacterProps {
  message?: string;
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export function LoadingCharacter({
  message = "잠시만 기다려주세요...",
  size = "md",
  isLoading = true,
}: LoadingCharacterProps) {
  const mood: CharacterMood = isLoading ? "loading" : "default";

  return <Character mood={mood} size={size} message={message} showMessage={true} />;
}
