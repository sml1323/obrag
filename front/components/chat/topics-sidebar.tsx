import React, { useState } from 'react';
import { Plus, Trash2, Folder, MessageSquare, X } from 'lucide-react';
import { Topic, ChatSession } from '@/lib/types/sessions';

interface TopicsSidebarProps {
  topics: Topic[];
  sessions: ChatSession[];
  currentSessionId: string | undefined;
  onSelectSession: (id: string) => void;
  onCreateSession: (topicId?: number) => void;
  onDeleteSession: (id: string) => void;
  onCreateTopic: (title: string) => void;
  onDeleteTopic: (id: number) => void;
  onSelectTopic: (id: number | null) => void;
  selectedTopicId: number | null;
  updateSession: (sessionId: string, data: { topic_id?: number | null, title?: string }) => void;
}

export function TopicsSidebar({
  topics,
  sessions,
  currentSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  onCreateTopic,
  onDeleteTopic,
  onSelectTopic,
  selectedTopicId,
  updateSession
}: TopicsSidebarProps) {
  const [newTopicName, setNewTopicName] = useState('');
  const [isCreatingTopic, setIsCreatingTopic] = useState(false);

  const handleCreateTopic = (e: React.FormEvent) => {
    e.preventDefault();
    if (newTopicName.trim()) {
      onCreateTopic(newTopicName);
      setNewTopicName('');
      setIsCreatingTopic(false);
    }
  };

  const filteredSessions = selectedTopicId
    ? sessions.filter(s => s.topic_id === selectedTopicId)
    : sessions.filter(s => !s.topic_id);

  const handleDragStart = (e: React.DragEvent, sessionId: string) => {
    e.dataTransfer.setData('sessionId', sessionId);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent, topicId: number | null) => {
    e.preventDefault();
    const sessionId = e.dataTransfer.getData('sessionId');
    if (sessionId) {
      updateSession(sessionId, { topic_id: topicId });
    }
  };

  return (
    <div className="w-[280px] bg-[#FFFEF0] border-r-4 border-black flex flex-col h-full">
      <div className="p-4 border-b-4 border-black">
        <button
          onClick={() => onCreateSession(selectedTopicId || undefined)}
          className="w-full bg-[#FF6B35] text-white border-2 border-black shadow-[4px_4px_0px_#000000] py-2 font-bold hover:translate-y-[2px] hover:shadow-[2px_2px_0px_#000000] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
        >
          <Plus className="h-5 w-5" /> NEW CHAT
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <h3 className="font-black text-sm uppercase tracking-widest mb-4 flex items-center justify-between">
            Topics
            <button 
              onClick={() => setIsCreatingTopic(true)}
              className="p-1 hover:bg-black hover:text-white transition-colors"
            >
              <Plus className="h-4 w-4" />
            </button>
          </h3>

          {isCreatingTopic && (
            <form onSubmit={handleCreateTopic} className="mb-4 flex gap-2">
              <input
                autoFocus
                type="text"
                value={newTopicName}
                onChange={(e) => setNewTopicName(e.target.value)}
                placeholder="Topic name..."
                className="w-full border-2 border-black p-1 text-sm focus:outline-none"
                onBlur={() => !newTopicName && setIsCreatingTopic(false)}
              />
            </form>
          )}

          <div className="space-y-2 mb-8">
            <div
              onClick={() => onSelectTopic(null)}
              onDragOver={handleDragOver}
              onDrop={(e) => handleDrop(e, null)}
              className={`
                cursor-pointer p-2 border-2 text-sm font-bold flex items-center gap-2 transition-colors
                ${selectedTopicId === null 
                  ? 'bg-black text-white border-black' 
                  : 'bg-white border-black hover:bg-gray-100'}
              `}
            >
              <MessageSquare className="h-4 w-4" />
              All / Uncategorized
            </div>
            
            {topics.map(topic => (
              <div
                key={topic.id}
                onClick={() => onSelectTopic(topic.id!)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, topic.id!)}
                className={`
                  group relative cursor-pointer p-2 border-2 text-sm font-bold flex items-center justify-between transition-all
                  ${selectedTopicId === topic.id 
                    ? 'bg-[#4ECDC4] border-black text-black shadow-[3px_3px_0px_#000000]' 
                    : 'bg-white border-black hover:translate-x-1'}
                `}
              >
                <span className="flex items-center gap-2 truncate">
                  <Folder className="h-4 w-4" />
                  {topic.title}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Delete topic?')) onDeleteTopic(topic.id!);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-red-500 hover:text-white transition-all"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>

          <h3 className="font-black text-sm uppercase tracking-widest mb-4 border-t-4 border-black pt-4">
            Sessions
          </h3>
          
          <div className="space-y-2">
            {filteredSessions.map(session => (
              <div
                key={session.id}
                draggable
                onDragStart={(e) => handleDragStart(e, session.id)}
                onClick={() => onSelectSession(session.id)}
                className={`
                  group cursor-pointer p-3 border-2 text-sm font-mono relative transition-all active:cursor-grabbing
                  ${currentSessionId === session.id 
                    ? 'bg-yellow-300 border-black shadow-[3px_3px_0px_#000000]' 
                    : 'bg-white border-gray-300 hover:border-black hover:shadow-sm'}
                `}
              >
                <div className="truncate pr-6">{session.title}</div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Delete chat?')) onDeleteSession(session.id);
                  }}
                  className="absolute right-1 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 p-1 hover:text-red-600"
                >
                  <Trash2 className="h-3 w-3" />
                </button>
              </div>
            ))}
            {filteredSessions.length === 0 && (
              <div className="text-xs text-gray-500 italic text-center py-4">
                No sessions here
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
