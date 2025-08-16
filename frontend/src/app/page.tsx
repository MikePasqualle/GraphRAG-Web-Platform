'use client';

import React, { useState, useEffect } from 'react';
import { 
  Upload, 
  FileText, 
  MessageSquare, 
  Network, 
  Settings,
  Menu,
  X
} from 'lucide-react';
import toast from 'react-hot-toast';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import FileUpload from '@/components/FileUpload';
import FileList from '@/components/FileList';
import ChatInterface from '@/components/ChatInterface';
import GraphVisualization from '@/components/GraphVisualization';
import IndexingStatus from '@/components/IndexingStatus';
import { cn } from '@/lib/utils';
import { api } from '@/lib/api';
import type { ChatMode } from '@/lib/types';

type View = 'files' | 'graph' | 'chat' | 'status';

const GraphRAGPlatform: React.FC = () => {
  const [currentView, setCurrentView] = useState<View>('files');
  const [selectedFiles, setSelectedFiles] = useState<string[]>([]);
  const [chatMode, setChatMode] = useState<ChatMode>('local');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [refreshTrigger, setRefreshTrigger] = useState(0);
  const [apiHealth, setApiHealth] = useState<boolean | null>(null);

  // Проверка здоровья API при загрузке
  useEffect(() => {
    const checkHealth = async () => {
      try {
        await api.general.health();
        setApiHealth(true);
      } catch {
        setApiHealth(false);
        toast.error('API недоступен. Проверьте подключение к серверу.');
      }
    };

    checkHealth();
  }, []);

  // Обработчики событий
  const handleFileSelect = (fileId: string) => {
    setSelectedFiles(prev => 
      prev.includes(fileId)
        ? prev.filter(id => id !== fileId)
        : [...prev, fileId]
    );
  };

  const handleFileUploadComplete = () => {
    setRefreshTrigger(prev => prev + 1);
    toast.success('Файл загружен и добавлен в очередь индексации');
  };

  const handleFileDelete = (fileId: string) => {
    setSelectedFiles(prev => prev.filter(id => id !== fileId));
    setRefreshTrigger(prev => prev + 1);
  };

  const handleViewChange = (view: View) => {
    setCurrentView(view);
    
    // Автоматическое переключение на local режим при переходе в чат
    if (view === 'chat' && selectedFiles.length > 0) {
      setChatMode('local');
    }
  };

  // Элементы навигации
  const navigationItems = [
    {
      id: 'files' as View,
      label: 'Файлы',
      icon: FileText,
      description: 'Управление файлами и загрузка',
    },
    {
      id: 'graph' as View,
      label: 'Граф',
      icon: Network,
      description: 'Визуализация графа знаний',
      disabled: selectedFiles.length === 0,
    },
    {
      id: 'chat' as View,
      label: 'Чат',
      icon: MessageSquare,
      description: 'Вопросы к документам',
    },
    {
      id: 'status' as View,
      label: 'Статус',
      icon: Settings,
      description: 'Статус индексации',
    },
  ];

  // Компонент навигации
  const Navigation = () => (
    <div className="space-y-2">
      {navigationItems.map((item) => {
        const Icon = item.icon;
        return (
          <Button
            key={item.id}
            variant={currentView === item.id ? 'default' : 'ghost'}
            className={cn(
              'w-full justify-start',
              item.disabled && 'opacity-50 cursor-not-allowed'
            )}
            onClick={() => !item.disabled && handleViewChange(item.id)}
            disabled={item.disabled}
          >
            <Icon className="w-4 h-4 mr-3" />
            <div className="text-left">
              <div className="font-medium">{item.label}</div>
              {sidebarOpen && (
                <div className="text-xs text-muted-foreground">
                  {item.description}
                </div>
              )}
            </div>
          </Button>
        );
      })}
    </div>
  );

  // Отрисовка контента по текущему виду
  const renderContent = () => {
    switch (currentView) {
      case 'files':
        return (
          <div className="space-y-6">
            <FileUpload
              onUploadComplete={handleFileUploadComplete}
              maxFiles={10}
              disabled={apiHealth === false}
            />
            <FileList
              selectedFiles={selectedFiles}
              onFileSelect={handleFileSelect}
              onFileDelete={handleFileDelete}
              refreshTrigger={refreshTrigger}
            />
          </div>
        );

      case 'graph':
        return (
          <div className="h-full">
            <GraphVisualization
              fileIds={selectedFiles}
              height="calc(100vh - 8rem)"
              onNodeSelect={(nodeId, nodeData) => {
                console.log('Node selected:', nodeId, nodeData);
              }}
              onEdgeSelect={(edgeId, edgeData) => {
                console.log('Edge selected:', edgeId, edgeData);
              }}
            />
          </div>
        );

      case 'chat':
        return (
          <div className="h-full">
            <ChatInterface
              selectedFiles={selectedFiles}
              onModeChange={setChatMode}
              className="h-[calc(100vh-8rem)]"
            />
          </div>
        );

      case 'status':
        return (
          <div className="space-y-6">
            <IndexingStatus autoRefresh={true} refreshInterval={3000} />
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="flex h-screen bg-background">
      {/* Боковая панель */}
      <div
        className={cn(
          'bg-card border-r border-border transition-all duration-300 flex flex-col',
          sidebarOpen ? 'w-80' : 'w-16'
        )}
      >
        {/* Заголовок */}
        <div className="p-4 border-b border-border">
          <div className="flex items-center justify-between">
            {sidebarOpen && (
              <div>
                <h1 className="text-xl font-bold">GraphRAG</h1>
                <p className="text-sm text-muted-foreground">Web Platform</p>
              </div>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSidebarOpen(!sidebarOpen)}
            >
              {sidebarOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
            </Button>
          </div>
        </div>

        {/* Навигация */}
        <div className="flex-1 p-4">
          <Navigation />
        </div>

        {/* Информация о выбранных файлах */}
        {sidebarOpen && selectedFiles.length > 0 && (
          <div className="p-4 border-t border-border">
            <div className="text-sm">
              <span className="font-medium">Выбрано файлов:</span>
              <span className="ml-2 text-muted-foreground">{selectedFiles.length}</span>
            </div>
            {currentView === 'chat' && (
              <div className="text-xs text-muted-foreground mt-1">
                Режим: {chatMode === 'local' ? 'Локальный' : 'Глобальный'}
              </div>
            )}
          </div>
        )}

        {/* Статус API */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center space-x-2 text-xs">
            <div
              className={cn(
                'w-2 h-2 rounded-full',
                apiHealth === true ? 'bg-green-500' :
                apiHealth === false ? 'bg-red-500' : 'bg-yellow-500'
              )}
            />
            <span className="text-muted-foreground">
              {apiHealth === true ? 'API активен' :
               apiHealth === false ? 'API недоступен' : 'Проверка API...'}
            </span>
          </div>
        </div>
      </div>

      {/* Основной контент */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Заголовок основной области */}
        <div className="p-6 border-b border-border bg-card">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold">
                {navigationItems.find(item => item.id === currentView)?.label}
              </h2>
              <p className="text-muted-foreground">
                {navigationItems.find(item => item.id === currentView)?.description}
              </p>
            </div>
            
            {/* Дополнительные действия */}
            <div className="flex items-center space-x-2">
              {currentView === 'graph' && selectedFiles.length > 0 && (
                <div className="text-sm text-muted-foreground">
                  Графическое представление {selectedFiles.length} файлов
                </div>
              )}
              
              {currentView === 'chat' && (
                <div className="flex items-center space-x-2">
                  <Button
                    variant={chatMode === 'local' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChatMode('local')}
                    disabled={selectedFiles.length === 0}
                  >
                    Локальный
                  </Button>
                  <Button
                    variant={chatMode === 'global' ? 'default' : 'outline'}
                    size="sm"
                    onClick={() => setChatMode('global')}
                  >
                    Глобальный
                  </Button>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Контент */}
        <div className="flex-1 p-6 overflow-auto">
          {apiHealth === false ? (
            <Card>
              <CardContent className="p-6 text-center">
                <div className="text-red-500 mb-4">
                  <Settings className="w-12 h-12 mx-auto mb-2" />
                  <h3 className="text-lg font-semibold">API недоступен</h3>
                  <p className="text-sm text-muted-foreground">
                    Не удается подключиться к серверу GraphRAG
                  </p>
                </div>
                <Button 
                  onClick={() => window.location.reload()}
                  variant="outline"
                >
                  Обновить страницу
                </Button>
              </CardContent>
            </Card>
          ) : (
            renderContent()
          )}
        </div>
      </div>
    </div>
  );
};

export default GraphRAGPlatform;
