'use client';

import React, { useState, useEffect } from 'react';
import { 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  Clock, 
  XCircle,
  Play,
  Pause,
  BarChart3
} from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn, formatPercentage, formatRelativeTime } from '@/lib/utils';
import { api } from '@/lib/api';
import type { IndexingProgress } from '@/lib/types';
import toast from 'react-hot-toast';

interface IndexingStatusProps {
  fileId?: string;
  onStatusChange?: (status: IndexingProgress) => void;
  className?: string;
  autoRefresh?: boolean;
  refreshInterval?: number;
}

const IndexingStatus: React.FC<IndexingStatusProps> = ({
  fileId,
  onStatusChange,
  className,
  autoRefresh = true,
  refreshInterval = 2000,
}) => {
  const [progress, setProgress] = useState<IndexingProgress | null>(null);
  const [allStatuses, setAllStatuses] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(autoRefresh);

  // Загрузка статуса для конкретного файла
  const loadFileStatus = async (id: string) => {
    try {
      setError(null);
      const status = await api.indexing.getStatus(id);
      setProgress(status);
      onStatusChange?.(status);
    } catch (err: any) {
      setError(err.message);
    }
  };

  // Загрузка всех статусов
  const loadAllStatuses = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await api.indexing.getAllStatuses();
      setAllStatuses(response.statuses || []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Эффект для загрузки данных
  useEffect(() => {
    if (fileId) {
      loadFileStatus(fileId);
    } else {
      loadAllStatuses();
    }
  }, [fileId]);

  // Автообновление
  useEffect(() => {
    if (!isRefreshing) return;

    const interval = setInterval(() => {
      if (fileId) {
        loadFileStatus(fileId);
      } else {
        loadAllStatuses();
      }
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [fileId, isRefreshing, refreshInterval]);

  // Управление процессом индексации
  const handleCancel = async (id: string) => {
    try {
      await api.indexing.cancel(id);
      toast.success('Индексация отменена');
      if (fileId) {
        loadFileStatus(fileId);
      } else {
        loadAllStatuses();
      }
    } catch (err: any) {
      toast.error(`Ошибка отмены: ${err.message}`);
    }
  };

  const handleRetry = async (id: string) => {
    try {
      await api.indexing.retry(id);
      toast.success('Индексация перезапущена');
      if (fileId) {
        loadFileStatus(fileId);
      } else {
        loadAllStatuses();
      }
    } catch (err: any) {
      toast.error(`Ошибка перезапуска: ${err.message}`);
    }
  };

  // Получение иконки статуса
  const getStatusIcon = (status: string, isActive = false) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'indexing':
        return <RefreshCw className={cn('w-5 h-5 text-blue-500', isActive && 'animate-spin')} />;
      case 'uploaded':
        return <Clock className="w-5 h-5 text-yellow-500" />;
      case 'cancelled':
        return <XCircle className="w-5 h-5 text-gray-500" />;
      default:
        return <Clock className="w-5 h-5 text-gray-500" />;
    }
  };

  // Получение текста статуса
  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Завершено';
      case 'error':
        return 'Ошибка';
      case 'indexing':
        return 'Индексация';
      case 'uploaded':
        return 'В очереди';
      case 'cancelled':
        return 'Отменено';
      default:
        return 'Неизвестно';
    }
  };

  // Получение описания текущего шага
  const getStepDescription = (step: string) => {
    switch (step) {
      case 'preparing':
        return 'Подготовка файла';
      case 'chunking':
        return 'Разбиение на части';
      case 'entity_extraction':
        return 'Извлечение сущностей';
      case 'relationship_extraction':
        return 'Извлечение связей';
      case 'community_detection':
        return 'Поиск сообществ';
      case 'finalizing':
        return 'Финализация';
      case 'finished':
        return 'Завершено';
      case 'failed':
        return 'Не удалось';
      default:
        return step;
    }
  };

  // Компонент прогресс-бара
  const ProgressBar: React.FC<{ progress: number; status: string }> = ({ progress, status }) => (
    <div className="w-full bg-gray-200 rounded-full h-2.5">
      <div
        className={cn(
          'h-2.5 rounded-full transition-all duration-500',
          status === 'error' ? 'bg-red-500' : 'bg-blue-500'
        )}
        style={{ width: `${Math.max(0, Math.min(100, progress))}%` }}
      />
    </div>
  );

  // Рендер для одного файла
  if (fileId && progress) {
    return (
      <Card className={className}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center">
              {getStatusIcon(progress.status, progress.status === 'indexing')}
              <span className="ml-2">Статус индексации</span>
            </CardTitle>
            <div className="flex items-center space-x-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsRefreshing(!isRefreshing)}
              >
                {isRefreshing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => loadFileStatus(fileId)}
              >
                <RefreshCw className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">
                {getStatusText(progress.status)}
              </span>
              <span className="text-sm text-muted-foreground">
                {formatPercentage(progress.progress_percentage)}
              </span>
            </div>
            <ProgressBar progress={progress.progress_percentage} status={progress.status} />
          </div>

          {progress.current_step && (
            <div>
              <span className="text-sm font-medium">Текущий шаг:</span>
              <p className="text-sm text-muted-foreground">
                {getStepDescription(progress.current_step)}
              </p>
            </div>
          )}

          {progress.estimated_remaining && (
            <div>
              <span className="text-sm font-medium">Осталось:</span>
              <p className="text-sm text-muted-foreground">
                ~{Math.round(progress.estimated_remaining / 60)} минут
              </p>
            </div>
          )}

          {progress.started_at && (
            <div>
              <span className="text-sm font-medium">Начато:</span>
              <p className="text-sm text-muted-foreground">
                {formatRelativeTime(progress.started_at)}
              </p>
            </div>
          )}

          {progress.error_message && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">{progress.error_message}</p>
            </div>
          )}

          {/* Действия */}
          <div className="flex space-x-2 pt-2">
            {progress.status === 'indexing' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleCancel(progress.file_id)}
              >
                Отменить
              </Button>
            )}
            {progress.status === 'error' && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleRetry(progress.file_id)}
              >
                Повторить
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    );
  }

  // Рендер для всех файлов
  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center">
            <BarChart3 className="w-5 h-5 mr-2" />
            Статусы индексации
          </CardTitle>
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsRefreshing(!isRefreshing)}
            >
              {isRefreshing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={loadAllStatuses}
              disabled={loading}
            >
              <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg mb-4">
            <p className="text-sm text-red-700">{error}</p>
          </div>
        )}

        {loading && allStatuses.length === 0 ? (
          <div className="text-center py-6">
            <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground mx-auto mb-2" />
            <p className="text-sm text-muted-foreground">Загрузка статусов...</p>
          </div>
        ) : allStatuses.length === 0 ? (
          <div className="text-center py-6 text-muted-foreground">
            <p>Нет файлов в обработке</p>
          </div>
        ) : (
          <div className="space-y-3">
            {allStatuses.map((status) => (
              <div
                key={status.file_id}
                className="border rounded-lg p-3 hover:bg-muted/50 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getStatusIcon(status.status, status.status === 'indexing')}
                    <span className="font-medium text-sm truncate">
                      {status.filename}
                    </span>
                  </div>
                  <span className="text-xs text-muted-foreground">
                    {formatPercentage(status.progress_percentage)}
                  </span>
                </div>

                <ProgressBar progress={status.progress_percentage} status={status.status} />

                <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
                  <span>{getStepDescription(status.current_step)}</span>
                  {status.upload_date && (
                    <span>{formatRelativeTime(status.upload_date)}</span>
                  )}
                </div>

                {status.error_message && (
                  <p className="text-xs text-red-600 mt-1">{status.error_message}</p>
                )}

                {status.status === 'completed' && (
                  <div className="flex items-center space-x-4 mt-2 text-xs text-muted-foreground">
                    {status.entities_count && (
                      <span>{status.entities_count} сущностей</span>
                    )}
                    {status.relationships_count && (
                      <span>{status.relationships_count} связей</span>
                    )}
                    {status.communities_count && (
                      <span>{status.communities_count} сообществ</span>
                    )}
                  </div>
                )}

                {/* Действия для конкретного файла */}
                {(status.status === 'indexing' || status.status === 'error') && (
                  <div className="flex space-x-2 mt-2">
                    {status.status === 'indexing' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleCancel(status.file_id)}
                      >
                        Отменить
                      </Button>
                    )}
                    {status.status === 'error' && (
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRetry(status.file_id)}
                      >
                        Повторить
                      </Button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default IndexingStatus;
