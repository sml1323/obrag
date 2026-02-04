import {
  createUIMessageStream,
  createUIMessageStreamResponse,
} from "ai";

export const maxDuration = 60;

export async function POST(req: Request) {
  try {
    const { messages, settings, session_id } = await req.json();

    if (!messages || messages.length === 0) {
      return new Response("No messages provided", { status: 400 });
    }

    const lastMessage = messages[messages.length - 1];
    const question =
      lastMessage.content ||
      lastMessage.parts
        ?.filter((p: { type: string }) => p.type === "text")
        .map((p: { text: string }) => p.text)
        .join("") ||
      "";

    if (!question) {
      return new Response("Empty message content", { status: 400 });
    }

    const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

    const requestBody: Record<string, unknown> = { question };

    if (session_id) requestBody.session_id = session_id;
    if (settings?.apiKey) requestBody.api_key = settings.apiKey;
    if (settings?.llmProvider) requestBody.llm_provider = settings.llmProvider;
    if (settings?.llmModel) requestBody.llm_model = settings.llmModel;

    const response = await fetch(`${backendUrl}/chat/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(requestBody),
    });

    if (!response.ok) {
      console.error(
        "[Chat Proxy] Backend error:",
        response.status,
        response.statusText
      );
      return new Response(`Backend Error: ${response.statusText}`, {
        status: response.status,
      });
    }

    return createUIMessageStreamResponse({
      stream: createUIMessageStream({
        async execute({ writer }) {
          const decoder = new TextDecoder();
          const reader = response.body?.getReader();

          if (!reader) {
            return;
          }

          const textId = `text-${Date.now()}`;
          writer.write({ type: "text-start", id: textId });

          try {
            let buffer = "";

            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              buffer += decoder.decode(value, { stream: true });
              const lines = buffer.split("\n\n");
              buffer = lines.pop() || "";

              for (const line of lines) {
                if (line.startsWith("data: ")) {
                  const dataStr = line.slice(6).trim();
                  if (!dataStr) continue;

                  try {
                    const data = JSON.parse(dataStr);

                    if (data.type === "content" && data.content) {
                      writer.write({
                        type: "text-delta",
                        id: textId,
                        delta: data.content,
                      });
                    } else if (data.type === "error") {
                      console.error("[Chat Proxy] Stream error:", data.message);
                    }
                  } catch {
                    /* malformed JSON */
                  }
                }
              }
            }

            if (buffer.startsWith("data: ")) {
              const dataStr = buffer.slice(6).trim();
              if (dataStr) {
                try {
                  const data = JSON.parse(dataStr);
                  if (data.type === "content" && data.content) {
                    writer.write({
                      type: "text-delta",
                      id: textId,
                      delta: data.content,
                    });
                  }
                } catch {
                  /* malformed JSON */
                }
              }
            }
          } catch (e) {
            console.error("[Chat Proxy] Stream reading error", e);
          }

          writer.write({ type: "text-end", id: textId });
        },
      }),
    });
  } catch (error) {
    console.error("[Chat Proxy] Internal error:", error);
    return new Response(JSON.stringify({ error: "Internal server error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
