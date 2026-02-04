import React, { useRef } from 'react';
import { Send } from 'lucide-react';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

export function MessageInput({ onSend, disabled }: MessageInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (disabled) return;

    const content = textareaRef.current?.value.trim();
    if (content) {
      onSend(content);
      if (textareaRef.current) {
        textareaRef.current.value = '';
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const adjustHeight = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 120) + 'px';
    }
  };

  return (
    <div className="bg-white border-t-4 border-black p-4 sticky bottom-0 z-10">
      <form onSubmit={handleSubmit} className="flex gap-4 max-w-4xl mx-auto">
        <textarea
          ref={textareaRef}
          rows={1}
          placeholder="Ask something about your vault..."
          className="flex-1 bg-white border-2 border-black p-3 resize-none focus:outline-none focus:shadow-[4px_4px_0px_#000000] transition-shadow disabled:bg-gray-100 disabled:cursor-not-allowed font-mono text-sm"
          onKeyDown={handleKeyDown}
          onInput={adjustHeight}
          disabled={disabled}
        />
        <button
          type="submit"
          disabled={disabled}
          className="bg-black text-white px-6 py-2 font-bold hover:bg-gray-800 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2 border-2 border-transparent active:border-black active:bg-white active:text-black transition-all"
        >
          <Send className="h-5 w-5" />
          SEND
        </button>
      </form>
    </div>
  );
}
