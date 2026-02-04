export async function GET() {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

  try {
    const response = await fetch(`${backendUrl}/para/projects`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      return new Response(await response.text(), { status: response.status });
    }

    return new Response(JSON.stringify(await response.json()), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[PARA API] Error:", error);
    return new Response(JSON.stringify({ error: "Failed to fetch PARA projects" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
