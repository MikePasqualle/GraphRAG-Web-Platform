'use client';

import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Bot, 
  User, 
  Settings, 
  Trash2, 
  Download,
  Globe,
  MapPin,
  Copy,
  ExternalLink
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import toast from 'react-hot-toast';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn, formatDate, copyToClipboard } from '@/lib/utils';
import { api, parseSSEStream } from '@/lib/api';
import type { ChatMessage, ChatMode, ChatQuery, ChatSource } from '@/lib/types';

interface ChatInterfaceProps {
  selectedFiles: string[];
  onModeChange?: (mode: ChatMode) => void;
  className?: string;
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  selectedFiles,
  onModeChange,
  className,
}) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [chatMode, setChatMode] = useState<ChatMode>('local');
  const [streamingMessage, setStreamingMessage] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Автоскрол до останнього повідомлення
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streamingMessage]);

  // Фокус на input при монтуванні
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleModeChange = (mode: ChatMode) => {
    setChatMode(mode);
    onModeChange?.(mode);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading || isStreaming) return;

    // Валідація для local режиму
    if (chatMode === 'local' && selectedFiles.length === 0) {
      toast.error('Для локального пошуку потрібно вибрати принаймні один файл');
      return;
    }

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: inputMessage.trim(),
      timestamp: new Date().toISOString(),
      mode: chatMode,
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    const query: ChatQuery = {
      message: userMessage.content,
      mode: chatMode,
      file_ids: chatMode === 'local' ? selectedFiles : [],
      stream: true,
    };

    try {
      // Використання streaming API
      const stream = await api.chat.stream(query);
      
      setIsStreaming(true);
      setStreamingMessage('');
      
      const assistantMessageId = `assistant-${Date.now()}`;
      let fullResponse = '';
      let sources: ChatSource[] = [];

      for await (const chunk of parseSSEStream(stream)) {
        if (chunk.error) {
          throw new Error(chunk.error);
        }

        if (chunk.content) {
          fullResponse += chunk.content;
          setStreamingMessage(fullResponse);
        }

        if (chunk.is_final) {
          sources = chunk.sources || [];
          break;
        }
      }

      // Додаємо фінальну відповідь до списку повідомлень
      const assistantMessage: ChatMessage = {
        id: assistantMessageId,
        role: 'assistant',
        content: fullResponse,
        timestamp: new Date().toISOString(),
        mode: chatMode,
        sources: sources,
      };

      setMessages(prev => [...prev, assistantMessage]);
      setStreamingMessage('');
      
    } catch (error: any) {
      console.error('Chat error:', error);
      
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: `Вибачте, сталася помилка: ${error.message}`,
        timestamp: new Date().toISOString(),
        mode: chatMode,
      };
      
      setMessages(prev => [...prev, errorMessage]);
      toast.error(`Помилка чату: ${error.message}`);
    } finally {
      setIsLoading(false);
      setIsStreaming(false);
      setStreamingMessage('');
    }
  };

  const handleClearChat = () => {
    setMessages([]);
    setStreamingMessage('');
    toast.success('Історія чату очищена');
  };

  const handleCopyMessage = async (content: string) => {
    const success = await copyToClipboard(content);
    if (success) {
      toast.success('Повідомлення скопійовано');
    } else {
      toast.error('Не вдалося скопіювати');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Заголовок чату */}
      <Card className="flex-shrink-0">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Чат з документами</CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleClearChat}
                disabled={messages.length === 0}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Очистити
              </Button>
            </div>
          </div>
          
          {/* Вибір режиму */}
          <div className="flex items-center space-x-2 mt-3">
            <span className="text-sm text-muted-foreground">Режим:</span>
            <div className="flex border rounded-md overflow-hidden">
              <Button
                variant={chatMode === 'local' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => handleModeChange('local')}
                className="rounded-none border-0"
              >
                <MapPin className="w-4 h-4 mr-2" />
                Локальний
              </Button>
              <Button
                variant={chatMode === 'global' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => handleModeChange('global')}
                className="rounded-none border-0"
              >
                <Globe className="w-4 h-4 mr-2" />
                Глобальний
              </Button>
            </div>
            
            {chatMode === 'local' && (
              <span className="text-xs text-muted-foreground">
                ({selectedFiles.length} файлів вибрано)
              </span>
            )}
          </div>
        </CardHeader>
      </Card>

      {/* Область повідомлень */}
      <Card className="flex-1 flex flex-col min-h-0 mt-4">
        <CardContent className="flex-1 p-0 overflow-hidden">
          <div className="h-full overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && !isStreaming && (
              <div className="text-center text-muted-foreground py-12">
                <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <h3 className="text-lg font-medium mb-2">Розпочніть розмову</h3>
                <p className="text-sm">
                  {chatMode === 'local' 
                    ? 'Поставте запитання про вибрані файли'
                    : 'Поставте загальне запитання по всіх документах'
                  }
                </p>
              </div>
            )}

            {messages.map((message) => (
              <MessageComponent
                key={message.id}
                message={message}
                onCopy={handleCopyMessage}
              />
            ))}

            {/* Streaming повідомлення */}
            {isStreaming && streamingMessage && (
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-blue-600" />
                </div>
                <div className="flex-1">
                  <div className="bg-muted rounded-lg p-3">
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      className="prose prose-sm max-w-none"
                    >
                      {streamingMessage}
                    </ReactMarkdown>
                    <div className="flex items-center mt-2">
                      <div className="animate-pulse flex space-x-1">
                        <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                      </div>
                      <span className="text-xs text-muted-foreground ml-2">
                        Набираю відповідь...
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </CardContent>

        {/* Поле вводу */}
        <div className="border-t p-4">
          <div className="flex space-x-2">
            <Input
              ref={inputRef}
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Напишіть ваше запитання..."
              disabled={isLoading || isStreaming}
              className="flex-1"
            />
            <Button
              onClick={handleSendMessage}
              disabled={!inputMessage.trim() || isLoading || isStreaming}
            >
              <Send className="w-4 h-4" />
            </Button>
          </div>
          
          {chatMode === 'local' && selectedFiles.length === 0 && (
            <p className="text-xs text-amber-600 mt-2">
              ⚠️ Для локального пошуку потрібно вибрати файли
            </p>
          )}
        </div>
      </Card>
    </div>
  );
};

// Компонент окремого повідомлення
interface MessageComponentProps {
  message: ChatMessage;
  onCopy: (content: string) => void;
}

const MessageComponent: React.FC<MessageComponentProps> = ({ message, onCopy }) => {
  const isUser = message.role === 'user';
  
  return (
    <div className={cn(
      'flex items-start space-x-3',
      isUser && 'flex-row-reverse space-x-reverse'
    )}>
      {/* Аватар */}
      <div className={cn(
        'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
        isUser ? 'bg-green-100' : 'bg-blue-100'
      )}>
        {isUser ? (
          <User className="w-4 h-4 text-green-600" />
        ) : (
          <Bot className="w-4 h-4 text-blue-600" />
        )}
      </div>

      {/* Контент повідомлення */}
      <div className={cn('flex-1 max-w-3xl', isUser && 'text-right')}>
        <div className={cn(
          'rounded-lg p-3',
          isUser 
            ? 'bg-primary text-primary-foreground ml-12'
            : 'bg-muted mr-12'
        )}>
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              className="prose prose-sm max-w-none dark:prose-invert"
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>

        {/* Метадані */}
        <div className={cn(
          'flex items-center space-x-2 mt-2 text-xs text-muted-foreground',
          isUser && 'justify-end'
        )}>
          <span>{formatDate(message.timestamp)}</span>
          {message.mode && (
            <>
              <span>•</span>
              <span className="capitalize">
                {message.mode === 'local' ? 'Локальний' : 'Глобальний'}
              </span>
            </>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onCopy(message.content)}
            className="h-auto p-1 text-muted-foreground hover:text-foreground"
          >
            <Copy className="w-3 h-3" />
          </Button>
        </div>

        {/* Джерела */}
        {message.sources && message.sources.length > 0 && (
          <div className="mt-3 p-3 bg-muted/50 rounded-lg">
            <h4 className="text-xs font-medium text-muted-foreground mb-2">
              Джерела інформації:
            </h4>
            <div className="space-y-1">
              {message.sources.map((source, index) => (
                <div key={index} className="text-xs text-muted-foreground">
                  <span className="font-medium">{source.filename}</span>
                  {source.relevance_score && (
                    <span className="ml-2">
                      (релевантність: {Math.round(source.relevance_score * 100)}%)
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatInterface;
