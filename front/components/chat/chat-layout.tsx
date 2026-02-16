import React, { useEffect, useState } from 'react';
import { MessageList } from './message-list';
import { MessageInput } from './message-input';
import { TopicsSidebar } from './topics-sidebar';
import { useChat } from '@/lib/hooks/use-chat';
import { useMascot } from '@/components/layout/mascot';
import { getSettings } from '@/lib/api/settings';
import { SettingsResponse } from '@/lib/types/settings';

export function ChatLayout() {
  const [settings, setSettings] = useState<SettingsResponse | null>(null);

  useEffect(() => {
    getSettings().then(setSettings).catch(console.error);
  }, []);

  const {
    sessions,
    topics,
    currentSessionId,
    messages,
    selectedTopicId,
    isStreaming,
    error,
    sendMessage,
    loadSession,
    createSession,
    deleteSession,
    createTopic,
    deleteTopic,
    setSelectedTopicId,
    fetchTopicsAndSessions: _fetchTopicsAndSessions,
    updateSession
  } = useChat();

  const { setMascotState } = useMascot();

  useEffect(() => {
    // Reset mascot when component mounts/unmounts
    return () => setMascotState('idle');
  }, [setMascotState]);

  return (
    <div className="flex h-[calc(100vh-64px)] bg-[#F0F0F0]">
      <TopicsSidebar
        topics={topics}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={loadSession}
        onCreateSession={createSession}
        onDeleteSession={deleteSession}
        onCreateTopic={createTopic}
        onDeleteTopic={deleteTopic}
        onSelectTopic={setSelectedTopicId}
        selectedTopicId={selectedTopicId}
        updateSession={updateSession}
      />

      <div className="flex-1 flex flex-col min-w-0 bg-[#F7F7F7]">
        {settings && (
          <div className="flex justify-end px-4 py-2 bg-[#F7F7F7] border-b-[3px] border-[#1a1a1a]">
             <div className="inline-flex items-center px-3 py-1 text-xs font-bold border-2 border-[#1a1a1a] bg-[#FF6B35] text-[#1a1a1a] shadow-[2px_2px_0px_0px_rgba(26,26,26,1)]">
               {settings.llm_provider} / {settings.llm_model}
             </div>
          </div>
        )}
        <div className="flex-1 flex flex-col overflow-hidden relative">
          {error && (
            <div className="bg-red-500 text-white p-2 text-center font-bold sticky top-0 z-50">
              Error: {error.message}
            </div>
          )}
          
          <MessageList 
            messages={messages} 
            isStreaming={isStreaming} 
          />
          
          <MessageInput 
            onSend={sendMessage} 
            disabled={isStreaming} 
          />
        </div>
      </div>
    </div>
  );
}
