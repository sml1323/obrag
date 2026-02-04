// Follow EXACT pattern from front/app/api/chat/route.ts

export async function GET(req: Request) {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  
  try {
    const url = new URL(req.url);
    const response = await fetch(`${backendUrl}/projects/${url.search}`, {
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
    console.error("[Projects API] Error:", error);
    return new Response(JSON.stringify({ error: "Failed to fetch projects" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}

export async function POST(req: Request) {
  const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";
  
  try {
    const body = await req.json();
    
    // Map frontend vaultPath to backend path
    const backendBody = {
      name: body.name,
      path: body.vaultPath || body.path,  // Accept both
      description: body.description,
    };
    
    const response = await fetch(`${backendUrl}/projects/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(backendBody),
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      return new Response(JSON.stringify(data), { 
        status: response.status,
        headers: { "Content-Type": "application/json" },
      });
    }
    
    return new Response(JSON.stringify(data), {
      status: 201,
      headers: { "Content-Type": "application/json" },
    });
  } catch (error) {
    console.error("[Projects API] Error:", error);
    return new Response(JSON.stringify({ error: "Failed to create project" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
