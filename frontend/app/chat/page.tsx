"use client";

import {
  Conversation,
  ConversationContent,
  ConversationEmptyState,
  ConversationScrollButton,
} from "@/components/ai-elements/conversation";
import { Loader } from "@/components/ai-elements/loader";
import {
  Message,
  MessageAction,
  MessageActions,
  MessageContent,
  MessageResponse,
} from "@/components/ai-elements/message";
import {
  PromptInput,
  PromptInputBody,
  PromptInputFooter,
  PromptInputMessage,
  PromptInputSubmit,
  PromptInputTextarea,
} from "@/components/ai-elements/prompt-input";
import { Suggestion, Suggestions } from '@/components/ai-elements/suggestion';

import { useChat } from "@ai-sdk/react";
import { CopyIcon, RefreshCcwIcon } from "lucide-react";
import { Fragment, useState } from "react";

const suggestions = [
  "Should I invest in buying Bitcoin now?",
  "what stocks are likely to perform well this quarter?",
  "BTC vs ETH - which is a better investment?",
]


export default function ChatPage() {
  const [input, setInput] = useState("");

  const { messages, sendMessage, status, regenerate} = useChat();

  const handleSubmit = (message: PromptInputMessage) => {
    const hasText = Boolean(message.text.trim());

    // Early return if there's no text to send
    if (!hasText) {
      return;
    }

    if (input.trim()) {
      sendMessage(
        { text: message.text.trim() },
      );
      setInput("");
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage({ text: suggestion });
  }


  return (
    <div className="max-w-4xl mx-auto p-6 relative size-full h-screen font-mono">
      <div className="flex flex-col h-full">
        <Conversation className="h-full">
          <ConversationContent>
            {
              messages.length === 0 ? (
                <ConversationEmptyState title="Hello there! 👋" description="I'm MarketSenseAI. How can I help you today?"/>
              ) : (
                messages.map((message, messageIndex) => (
<Fragment key={message.id}>
                {message.parts.map((part, partIndex) => {
                  switch (part.type) {
                    case "text":
                      const isLastMessage =
                        messages.length - 1 === messageIndex;

                      return (
                        <Fragment key={`${message.id}-${partIndex}`}>
                          <Message from={message.role}>
                            <MessageContent>
                              <MessageResponse>{part.text}</MessageResponse>
                            </MessageContent>
                          </Message>
                          {message.role === "assistant" && isLastMessage && (
                            <MessageActions>
                              <MessageAction
                                onClick={() => regenerate()}
                                label="Retry"
                              >
                                <RefreshCcwIcon className="size-3" />
                              </MessageAction>
                              <MessageAction
                                onClick={() =>
                                  navigator.clipboard.writeText(part.text)
                                }
                                label="Copy"
                              >
                                <CopyIcon className="size-3" />
                              </MessageAction>
                            </MessageActions>
                          )}
                        </Fragment>
                      );
                    default:
                      return null;
                  }
                })}
              </Fragment>
                ))
              )
            }
            
            {status === "submitted" && <Loader />}
          </ConversationContent>
          <ConversationScrollButton />
        </Conversation>

        <div className="grid shrink-0 gap-4 pt-4">
          <Suggestions className="px-4">
          {suggestions.map((suggestion) => (
            <Suggestion
              key={suggestion}
              onClick={() => handleSuggestionClick(suggestion)}
              suggestion={suggestion}
            />
          ))}
        </Suggestions>
        </div>

        <PromptInput
          onSubmit={handleSubmit}
          className="mt-4 w-full max-w-2xl mx-auto relative"
          globalDrop
          multiple
        >
          <PromptInputBody>
            <PromptInputTextarea
              value={input}
              onChange={(e) => setInput(e.currentTarget.value)}
              placeholder="Type your message..."
              className="pr-12"
            />
          </PromptInputBody>
          <PromptInputFooter>
          </PromptInputFooter>
          <PromptInputSubmit
            status={status === "streaming" ? "streaming" : "ready"}
            disabled={!input.trim() && !status}
            className="absolute bottom-1 right-1 bg-blue-500"
          />
        </PromptInput>
      </div>
    </div>
  );
}