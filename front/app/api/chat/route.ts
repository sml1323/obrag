import {
  convertToModelMessages,
  streamText,
  type UIMessage,
} from "ai";

export const maxDuration = 60;

export async function POST(req: Request) {
  try {
    const { messages, settings }: { 
      messages: UIMessage[]; 
      settings?: {
        llmProvider: string;
        llmModel: string;
        apiKey: string;
      } 
    } = await req.json();

    console.log("[v0] Chat API request received", { 
      messageCount: messages.length, 
      provider: settings?.llmProvider 
    });

    // For demo purposes, return mock streaming response if no API key
    if (!settings?.apiKey && settings?.llmProvider !== "ollama") {
      console.log("[v0] No API key provided, returning demo response");
      
      const encoder = new TextEncoder();
      const stream = new ReadableStream({
        async start(controller) {
          const demoMessage = "안녕하세요! 현재 데모 모드로 실행 중입니다. 실제 AI 응답을 받으려면 설정에서 API 키를 입력해주세요.\n\n설정 방법:\n1. 우측 하단 설정 아이콘 클릭\n2. LLM API Key 입력\n3. 원하는 모델 선택";
          
          // Send text chunks
          for (const char of demoMessage) {
            controller.enqueue(encoder.encode(`0:${JSON.stringify({ type: "text-delta", delta: char })}\n`));
            await new Promise(resolve => setTimeout(resolve, 20));
          }
          
          // Send finish
          controller.enqueue(encoder.encode(`0:${JSON.stringify({ type: "finish", finishReason: "stop" })}\n`));
          controller.close();
        }
      });

      return new Response(stream, {
        headers: {
          "Content-Type": "text/event-stream",
          "Cache-Control": "no-cache",
          "Connection": "keep-alive",
        },
      });
    }

    const systemPrompt = `당신은 Obsidian AI 어시스턴트입니다. 사용자의 Obsidian 노트를 기반으로 질문에 답변합니다.

주요 역할:
1. 사용자의 노트 내용을 기반으로 정확한 정보를 제공합니다.
2. 관련 노트를 연결하여 지식 그래프를 활용합니다.
3. 에빙하우스 망각곡선에 따라 복습이 필요한 내용을 추천합니다.
4. PARA 방법론(Projects, Areas, Resources, Archive)에 맞춰 정보를 구조화합니다.

답변 스타일:
- 친근하고 도움이 되는 톤으로 대화합니다.
- 가능하면 구체적인 예시와 함께 설명합니다.
- 노트 간의 연결고리를 발견하면 알려줍니다.
- 복습이 필요한 개념이 있다면 자연스럽게 상기시켜줍니다.

현재는 데모 모드입니다. 실제 노트 연동은 Vault 경로 설정 후 가능합니다.`;

    // Determine model based on settings
    const modelString = settings?.llmProvider === "ollama" 
      ? `ollama/${settings.llmModel}`
      : settings?.llmProvider === "gemini"
      ? `google/${settings.llmModel}`
      : `openai/${settings?.llmModel || "gpt-4o"}`;

    console.log("[v0] Using model:", modelString);

    const result = streamText({
      model: modelString,
      system: systemPrompt,
      messages: await convertToModelMessages(messages),
      abortSignal: req.signal,
    });

    return result.toUIMessageStreamResponse({
      originalMessages: messages,
    });
  } catch (error) {
    console.error("[v0] Chat API error:", error);
    return new Response(JSON.stringify({ error: "Internal server error" }), {
      status: 500,
      headers: { "Content-Type": "application/json" },
    });
  }
}
