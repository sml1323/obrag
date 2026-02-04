export async function GET(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  const { id } = await params;
  
  try {
    const response = await fetch(`${backendUrl}/projects/${id}`, {
      headers: { "Content-Type": "application/json" },
    });
    
    if (!response.ok) {
      return new Response(await response.text(), { status: response.status });
    }
    
    return new Response(JSON.stringify(await response.json()), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Projects API] Error:", error);
    return new Response(JSON.stringify({ error: "Failed to get project" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

export async function PATCH(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  const { id } = await params;
  
  try {
    const body = await req.json();
    
    const response = await fetch(`${backendUrl}/projects/${id}`, {
      method: "PATCH",
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
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Projects API] Error:", error);
    return new Response(JSON.stringify({ error: "Failed to update project" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

export async function DELETE(
  req: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  const { id } = await params;
  
  try {
    const response = await fetch(`${backendUrl}/projects/${id}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
    });
    
    if (!response.ok) {
      return new Response(await response.text(), { status: response.status });
    }
    
    return new Response(JSON.stringify({ ok: true }), {
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Projects API] Error:", error);
    return new Response(JSON.stringify({ error: "Failed to delete project" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
