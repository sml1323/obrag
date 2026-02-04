export async function POST(req: Request) {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  
  try {
    const url = new URL(req.url);
    
    let body = {};
    try {
      body = await req.json();
    } catch {
      // No body is fine
    }
    
    const response = await fetch(`${backendUrl}/sync/trigger${url.search}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      return new Response(JSON.stringify(data), { 
        status: response.status,
        headers: { "Content-Type": "application/json" },
      });
    }
    
    return new Response(JSON.stringify(data), {
      status: 200,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Sync API] Error:", error);
    return new Response(JSON.stringify({ error: "Failed to trigger sync" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
