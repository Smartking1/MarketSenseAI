import { google } from "@ai-sdk/google";
import { streamText } from "ai";

export const runtime = "edge";

export async function POST(req: Request) {
  const body = await req.json();

  const { messages, asset, timeframe }: { messages: UIMessage[]; asset?: string; timeframe?: string } = body;

  console.log("Received request with body:", body);  

  if (
    !Array.isArray(messages) ||
    messages.length === 0 ||
    !messages[messages.length - 1] ||
    !Array.isArray(messages[messages.length - 1].parts)
  ) {
    return new Response("Invalid message format", { status: 400 });
  }

  const lastMessage = messages[messages.length - 1].parts.find(
    (part) => part.type === "text"
  );
  
  if (!lastMessage || !lastMessage.text) {
    return new Response("Invalid message format", { status: 400 });
  }

  // Validate required parameters
  if (!asset || !timeframe) {
    return new Response("Asset and timeframe are required", { status: 400 });
  }

  try {
    const response = await fetch(
      `${process.env.NEXT_PUBLIC_BASE_API_URL}/analyze`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: lastMessage.text,
          asset: asset,
          timeframe: timeframe,
        }),
      }
    );

    if (!response.ok) {
      return new Response("Error from backend", { status: 500 });
    }

    const analysisData = await response.json();
    console.log("Response from backend:", analysisData);

    const result = streamText({
      model: google("gemini-2.5-flash"),
      system:
        "You are MarketSenseAI, a professional financial analyst assistant. Format your responses in clear, structured sections using markdown. First give a summary of the analysis to the user and then present the details in an easy-to-understand format. Be concise but comprehensive.",
      messages: [
        {
          role: "user",
          content: `Based on this comprehensive market analysis for ${asset} (${timeframe} timeframe), provide a clear investment recommendation:

${JSON.stringify(analysisData, null, 2)}

Format your response with clear sections and actionable insights.`,
        },
      ],
    });

    return result.toUIMessageStreamResponse();
  } catch (error) {
    console.error("Error processing request:", error);
    return new Response(
      JSON.stringify({
        error: "Failed to process the request.",
      }),
      { status: 500 }
    );
  }
}