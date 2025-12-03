import { convertToModelMessages, UIMessage } from "ai";

export async function POST(req:Request) {
    const { messages}: {messages: UIMessage[]} = await req.json();

    console.log("Received messages:", convertToModelMessages(messages));

    return new Response(JSON.stringify({ reply: "This is a static response from the API." }), {
        headers: { "Content-Type": "application/json" },
    });
}