import React from 'react';
import { SourceChunk, TokenUsage } from '@/lib/types/chat';
import { SourcesAccordion } from './sources-accordion';
import { Bot, User } from 'lucide-react';

interface MessageItemProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    sources?: SourceChunk[];
    usage?: TokenUsage;
  };
  isStreaming?: boolean;
}

export function MessageItem({ message, isStreaming }: MessageItemProps) {
  const isUser = message.role === 'user';

  return (
    <div className={`flex w-full mb-6 ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div 
        className={`
          max-w-[80%] 
          border-2 border-black 
          shadow-[6px_6px_0px_#000000] 
          p-4 
          ${isUser ? 'bg-[#FF6B35] text-white' : 'bg-[#4ECDC4] text-black'}
        `}
      >
        <div className="flex items-center gap-2 mb-2 border-b-2 border-black/20 pb-2">
          {isUser ? <User className="h-5 w-5" /> : <Bot className="h-5 w-5" />}
          <span className="font-bold uppercase tracking-wider text-sm">
            {isUser ? 'You' : 'Assistant'}
          </span>
        </div>
        
        <div className="whitespace-pre-wrap font-mono text-sm leading-relaxed">
          {message.content}
          {isStreaming && (
            <span className="inline-block w-2 h-4 bg-black ml-1 animate-pulse align-middle" />
          )}
        </div>

        {!isUser && message.sources && message.sources.length > 0 && (
          <div className="mt-4 pt-2 border-t-2 border-black/10">
            <SourcesAccordion sources={message.sources} />
          </div>
        )}

        {!isUser && message.usage && (message.usage.input_tokens > 0 || message.usage.output_tokens > 0) && (
          <div className="mt-3 pt-2 border-t-2 border-black/10 flex items-center gap-3">
            <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border border-black/30 bg-black/10">
              IN {message.usage.input_tokens.toLocaleString()}
            </span>
            <span className="inline-flex items-center px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider border border-black/30 bg-black/10">
              OUT {message.usage.output_tokens.toLocaleString()}
            </span>
            <span className="text-[10px] font-bold opacity-60">
              = {(message.usage.input_tokens + message.usage.output_tokens).toLocaleString()} tokens
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
