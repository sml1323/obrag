"use client";

import { SettingsForm } from "@/components/settings/settings-form";

export default function SettingsPage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-black mb-6 uppercase">Settings</h1>
      <SettingsForm />
    </div>
  );
}
