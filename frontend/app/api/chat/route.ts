import { google } from "@ai-sdk/google";
import { streamText, UIMessage } from "ai";

export const runtime = "edge";

export async function POST(req:Request) {
    const { messages}: { messages: UIMessage[] } = await req.json();
    const lastMessage = messages[messages.length - 1].parts.find(part => part.type === "text")!;

    try {
    const response = await fetch(`${process.env.NEXT_PUBLIC_BASE_API_URL}/analyze`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            query: lastMessage.text
        }) ,
    })

    if (!response.ok) {
        return new Response("Error from backend", { status: 500 });
    }
    
    const analysisData = await response.json();
    console.log("Response from backend:", analysisData);

    const result = streamText({
        model: google("gemini-2.5-flash"),
        system: "You are MarketSenseAI, a professional financial analyst assistant. Format your responses in clear, structured sections using markdown.First give a summary of the analysis to the user and then present the details in an easy-to-understand format. Be concise but comprehensive.",
        messages: [
            {
          role: 'user',
          content: `Based on this comprehensive market analysis, provide a clear investment recommendation:

${JSON.stringify(analysisData, null, 2)}

Format your response with clear sections and actionable insights.`,
        },
        ],
    })
    
    return result.toUIMessageStreamResponse();
    }
    catch (error) {
        console.error("Error processing request:", error);
        return new Response(JSON.stringify({
            error: 'Failed to process the request.',
        }), { status: 500});
    }
}