import React, { useEffect } from 'react';
import { MessageList } from './message-list';
import { MessageInput } from './message-input';
import { TopicsSidebar } from './topics-sidebar';
import { useChat } from '@/lib/hooks/use-chat';
import { useMascot } from '@/components/layout/mascot';

export function ChatLayout() {
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
