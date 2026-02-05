import React from 'react';
import { SourceChunk } from '@/lib/types/chat';
import { SourcesAccordion } from './sources-accordion';
import { Bot, User } from 'lucide-react';

interface MessageItemProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    sources?: SourceChunk[];
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
      </div>
    </div>
  );
}
