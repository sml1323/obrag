import React, { useEffect, useRef } from 'react';
import { Message } from '@/lib/types/sessions';
import { SourceChunk } from '@/lib/types/chat';
import { MessageItem } from './message-item';
import { BouncingMascot } from '@/components/ui/bouncing-mascot';

interface ExtendedMessage extends Omit<Message, 'role'> {
  role: 'user' | 'assistant';
  sources?: SourceChunk[];
}

interface MessageListProps {
  messages: ExtendedMessage[];
  isStreaming: boolean;
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isStreaming]);

  return (
    <div className="flex-1 overflow-y-auto p-6 space-y-6">
      <div className="max-w-4xl mx-auto pb-4">
        {messages.length === 0 ? (
          <div className="absolute inset-0 z-0">
            <BouncingMascot />
          </div>
        ) : (
          messages.map((msg, idx) => (
            <MessageItem 
              key={msg.id || idx} 
              message={msg}
              isStreaming={isStreaming && idx === messages.length - 1 && msg.role === 'assistant'}
            />
          ))
        )}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
