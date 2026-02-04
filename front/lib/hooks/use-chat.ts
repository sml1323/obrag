import { useState, useCallback, useEffect } from 'react';
import { useSSE } from './use-sse';
import { SSEEvent, SourceChunk } from '@/lib/types/chat';
import { Message, ChatSession, Topic } from '@/lib/types/sessions';
import * as SessionAPI from '@/lib/api/sessions';
import * as TopicAPI from '@/lib/api/topics';
import { BACKEND_URL } from '@/lib/api/client';
import { useMascot } from '@/components/layout/mascot';

interface ExtendedMessage extends Omit<Message, 'role'> {
  role: 'user' | 'assistant';
  sources?: SourceChunk[];
}

export function useChat() {
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [topics, setTopics] = useState<Topic[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string>();
  const [messages, setMessages] = useState<ExtendedMessage[]>([]);
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null);
  
  const { startStream, stopStream: _stopStream, isStreaming, error } = useSSE<SSEEvent>();
  const { setMascotState } = useMascot();

  const fetchTopicsAndSessions = useCallback(async () => {
    try {
      const [t, s] = await Promise.all([
        TopicAPI.listTopics(),
        SessionAPI.listSessions()
      ]);
      setTopics(t);
      setSessions(s);
    } catch (e) {
      console.error('Failed to load initial data', e);
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string) => {
    try {
      const msgs = await SessionAPI.getSessionMessages(sessionId);
      setMessages(msgs.map(m => ({ ...m, role: m.role as 'user' | 'assistant' })));
      setCurrentSessionId(sessionId);
    } catch (e) {
      console.error('Failed to load session', e);
    }
  }, []);

  const createSession = useCallback(async (topicId?: number) => {
    try {
      const newSession = await SessionAPI.createSession({ 
        title: 'New Chat',
        topic_id: topicId 
      });
      setSessions(prev => [newSession, ...prev]);
      setCurrentSessionId(newSession.id);
      setMessages([]);
      return newSession.id;
    } catch (e) {
      console.error('Failed to create session', e);
    }
  }, []);

  const deleteSession = useCallback(async (id: string) => {
    try {
      await SessionAPI.deleteSession(id);
      setSessions(prev => prev.filter(s => s.id !== id));
      if (currentSessionId === id) {
        setCurrentSessionId(undefined);
        setMessages([]);
      }
    } catch (e) {
      console.error('Failed to delete session', e);
    }
  }, [currentSessionId]);

  const createTopic = useCallback(async (title: string) => {
    try {
      const newTopic = await TopicAPI.createTopic({ title });
      setTopics(prev => [...prev, newTopic]);
    } catch (e) {
      console.error('Failed to create topic', e);
    }
  }, []);

  const deleteTopic = useCallback(async (id: number) => {
    try {
      await TopicAPI.deleteTopic(id);
      setTopics(prev => prev.filter(t => t.id !== id));
      if (selectedTopicId === id) setSelectedTopicId(null);
      fetchTopicsAndSessions(); 
    } catch (e) {
      console.error('Failed to delete topic', e);
    }
  }, [selectedTopicId, fetchTopicsAndSessions]);

  const updateSession = useCallback(async (sessionId: string, data: { topic_id?: number | null, title?: string }) => {
    try {
      const updated = await SessionAPI.updateSession(sessionId, data);
      setSessions(prev => prev.map(s => s.id === sessionId ? updated : s));
      return updated;
    } catch (e) {
      console.error('Failed to update session', e);
    }
  }, []);

  const sendMessage = async (content: string) => {
    let sessionId = currentSessionId;
    
    if (!sessionId) {
      sessionId = await createSession(selectedTopicId || undefined);
      if (!sessionId) return;
    }

    const userMsg: ExtendedMessage = {
      role: 'user',
      content,
      created_at: new Date().toISOString()
    };
    
    setMessages(prev => [...prev, userMsg]);
    setMascotState('loading');

    // Optimistically add empty assistant message
    const assistantMsgId = Date.now();
    setMessages(prev => [
      ...prev,
      { role: 'assistant', content: '', id: assistantMsgId }
    ]);

    let fullAnswer = '';
    let sources: SourceChunk[] = [];

    await startStream(
      `${BACKEND_URL}/chat/stream`,
      {
        question: content,
        session_id: sessionId
      },
      (event: SSEEvent) => {
        if (event.type === 'start') {
          setMascotState('speaking');
          sources = event.sources;
        } else if (event.type === 'content') {
          fullAnswer += event.content;
          setMessages(prev => 
            prev.map(msg => 
              msg.id === assistantMsgId 
                ? { ...msg, content: fullAnswer, sources }
                : msg
            )
          );
        } else if (event.type === 'done') {
          setMascotState('idle');
        }
      }
    );
  };

  useEffect(() => {
    fetchTopicsAndSessions();
  }, [fetchTopicsAndSessions]);

  return {
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
    fetchTopicsAndSessions,
    updateSession
  };
}
