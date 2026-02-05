'use client';

import { ChatBubble, ChatBubbleAction, ChatBubbleAvatar, ChatBubbleMessage } from '@/components/ui/chat/chat-bubble';
import { ChatInput } from '@/components/ui/chat/chat-input';
import { ChatMessageList } from '@/components/ui/chat/chat-message-list';
import { Button } from '@/components/ui/button';
import { CopyIcon, CornerDownLeft, RefreshCcw, Volume2 } from 'lucide-react';
import { useEffect, useRef, useState } from 'react';
// import styles from './markdown-styles.module.css';
import styles from './markdown-styles-1.module.css';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import CodeDisplayBlock from '@/components/code-display-block';
import { SidebarInset, SidebarProvider, SidebarTrigger } from '@/components/ui/sidebar';
import { ChatSessionSidebar } from './chat-session-sidebar';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LoadingState } from '@/components/ui/loading-state';
import { getErrorMessage } from '@/lib/error-messages';

const apiBase = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '');

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
}

const ChatAiIcons = [
  {
    icon: CopyIcon,
    label: 'Copy',
  },
  {
    icon: RefreshCcw,
    label: 'Refresh',
  },
  {
    icon: Volume2,
    label: 'Volume',
  },
];

export default function ChatPage() {
  const [isGenerating, setIsGenerating] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: '1',
      role: 'assistant',
      content: 'Hello! I am your AI assistant for procurement risk analysis. How can I assist you today?',
    },
  ]);
  const [input, setInput] = useState('');

  const messagesRef = useRef<HTMLDivElement>(null);
  const formRef = useRef<HTMLFormElement>(null);

  useEffect(() => {
    if (messagesRef.current) {
      messagesRef.current.scrollTop = messagesRef.current.scrollHeight;
    }
  }, [messages]);

  const onKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (isGenerating || !input) return;
      setIsGenerating(true);
      handleSubmit(e as unknown as React.FormEvent<HTMLFormElement>);
    }
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || isGenerating) return;

    const messageText = input.trim();
    // Add user message
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      role: 'user',
      content: messageText,
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsGenerating(true);

    try {
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Request timeout')), 35000)
      );

      const fetchPromise = fetch(`${apiBase}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId,
        }),
      });

      const response = (await Promise.race([fetchPromise, timeoutPromise])) as Response;

      if (!response.ok) {
        const errorData = await response.json();
        const errorText = getErrorMessage(response.status, errorData?.error || errorData?.detail);
        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `❌ Error: ${errorText}`,
        };
        setMessages((prev) => [...prev, errorMessage]);
        setIsGenerating(false);
        return;
      }

      const data = await response.json();

      if (data.success) {
        if (data.session_id) {
          setSessionId(data.session_id);
        }

        const botMessage: ChatMessage = {
          id: data.session_id || Date.now().toString(),
          role: 'assistant',
          content: data.message || 'No response received',
        };
        setMessages((prev) => [...prev, botMessage]);
      } else {
        const errorMessage: ChatMessage = {
          id: Date.now().toString(),
          role: 'assistant',
          content: `❌ Error: ${data.error || 'Something went wrong'}`,
        };
        setMessages((prev) => [...prev, errorMessage]);
      }
    } catch (error) {
      const errorText = error instanceof Error ? error.message : 'Unknown error';
      const isTimeout = errorText.toLowerCase().includes('timeout') || errorText.toLowerCase().includes('too long');
      const friendlyMessage = isTimeout
        ? 'Request took too long. Try a shorter message or simpler query.'
        : 'Failed to connect to the server. Please check your connection and try again.';

      const errorMessage: ChatMessage = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `❌ Error: ${friendlyMessage}`,
      };
      setMessages((prev) => [...prev, errorMessage]);
      console.error('Chat error:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleActionClick = async (action: string, messageIndex: number) => {
    console.log('Action clicked:', action, 'Message index:', messageIndex);
    if (action === 'Refresh') {
      setIsGenerating(true);
      try {
        // Reload logic would go here
      } catch (error) {
        console.error('Error reloading:', error);
      } finally {
        setIsGenerating(false);
      }
    }

    if (action === 'Copy') {
      const message = messages[messageIndex];
      if (message && message.role === 'assistant') {
        navigator.clipboard.writeText(message.content);
      }
    }
  };

  const loadSession = async (id: string) => {
    console.log('Loading session:', id);
    try {
      const response = await fetch(`${apiBase}/chat/session/${id}`);
      const data = await response.json();
      console.log('Session data:', data);

      if (!response.ok || data?.success === false) {
        setMessages([
          {
            id: Date.now().toString(),
            role: 'assistant',
            content: data?.error || 'Failed to load session.',
          },
        ]);
        setIsGenerating(false);
        return;
      }

      // Transform the API response into chat messages
      const transformedMessages = Array.isArray(data.messages)
        ? data.messages.map((msg: any) => ({
            id: msg.id || `${Date.now()}-${Math.random().toString(36).slice(2)}`,
            role: msg.role === 'user' ? 'user' : 'assistant',
            content: msg.content || '',
          }))
        : [];

      // Only update messages if we have some, otherwise keep the welcome message
      if (transformedMessages.length > 0) {
        setMessages(transformedMessages);
      }
      setSessionId(id);
      setIsGenerating(false); // Ensure generating state is reset
      setInput(''); // Clear any existing input
    } catch (error) {
      console.error('Error loading chat logs:', error);
    }
  };

  return (
    <SidebarProvider>
      <ChatSessionSidebar variant="inset" onSessionSelect={loadSession} />
      <SidebarInset>
        <main className="flex h-[90vh] px-2 pt-4 w-full flex-col items-center">
          <div className="flex items-center gap-2 px-4 pb-4 justify-start w-full">
            <SidebarTrigger />
            {!sessionId && <p className="text-lg font-bold">New Chat</p>}
            {sessionId && (
              <div className="flex items-center gap-2">
                <Badge variant="outline">
                  ID: {sessionId}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="ml-2 h-4 w-4 cursor-pointer hover:bg-blue-300 hover:text-blue-700"
                    onClick={() => navigator.clipboard.writeText(sessionId)}
                  >
                    <CopyIcon className="h-3 w-3" />
                  </Button>
                </Badge>
              </div>
            )}
          </div>

          <ScrollArea className="flex-1 w-full h-[60vh]">
            <ChatMessageList>
              {/* Messages */}
              {messages &&
                messages.map((message, index) => (
                  <ChatBubble key={index} variant={message.role == 'user' ? 'sent' : 'received'}>
                    <ChatBubbleAvatar src="" fallback={message.role == 'user' ? '👩🏻' : '🤖'} />
                    <ChatBubbleMessage>
                      {message.content.split('```').map((part: string, index: number) => {
                        if (index % 2 === 0) {
                          return message.role === 'user' ? (
                            <p key={index}>{part}</p>
                          ) : (
                            <div key={index} className={`!text-default ${styles['markdown-body']}`}>
                              <Markdown remarkPlugins={[remarkGfm]}>{part}</Markdown>
                            </div>
                            // <div>{part.replace(/[\r\n]+/g, ' ')}</div>
                          );
                        } else {
                          return (
                            <pre className="whitespace-pre-wrap pt-2" key={index}>
                              <CodeDisplayBlock code={part} lang="" />
                            </pre>
                          );
                        }
                      })}

                      {message.role === 'assistant' && (
                        <div className="flex items-center mt-1.5 gap-1">
                          {!isGenerating && (
                            <>
                              {ChatAiIcons.map((icon, iconIndex) => {
                                const Icon = icon.icon;
                                return (
                                  <ChatBubbleAction
                                    variant="outline"
                                    className="size-5"
                                    key={iconIndex}
                                    icon={<Icon className="size-3" />}
                                    onClick={() => handleActionClick(icon.label, index)}
                                  />
                                );
                              })}
                            </>
                          )}
                        </div>
                      )}
                    </ChatBubbleMessage>
                  </ChatBubble>
                ))}

              {/* Loading */}
              {isGenerating && (
                <ChatBubble variant="received">
                  <ChatBubbleAvatar src="" fallback="🤖" />
                  <ChatBubbleMessage>
                    <LoadingState message="AI is analyzing your question..." />
                  </ChatBubbleMessage>
                </ChatBubble>
              )}
            </ChatMessageList>
          </ScrollArea>
          {/* Form and Footer fixed at the bottom */}
          <div className="w-full px-4 pb-4">
            <form
              ref={formRef}
              onSubmit={handleSubmit}
              className="relative rounded-lg border bg-background focus-within:ring-1 focus-within:ring-ring"
            >
              <ChatInput
                value={input}
                onKeyDown={onKeyDown}
                onChange={handleInputChange}
                placeholder="Type your message here..."
                className="rounded-lg bg-background border-0 shadow-none focus-visible:ring-0"
              />
              <div className="flex items-center p-3 pt-0 dark:bg-input/30">
                <Button disabled={!input || isGenerating} type="submit" size="sm" className="ml-auto gap-1.5">
                  Send Message
                  <CornerDownLeft className="size-3.5" />
                </Button>
              </div>
            </form>
          </div>
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
