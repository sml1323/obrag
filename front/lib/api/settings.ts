import { request } from "./client";
import { SettingsResponse, SettingsUpdate } from "../types/settings";

export async function getSettings(): Promise<SettingsResponse> {
  return request<SettingsResponse>("/settings");
}

export async function updateSettings(
  data: SettingsUpdate,
): Promise<SettingsResponse> {
  return request<SettingsResponse>("/settings", {
    method: "PUT",
    body: JSON.stringify(data),
  });
}
