'use client';

import React, { useState, useEffect } from 'react';
import { 
  File, 
  Download, 
  Trash2, 
  Eye, 
  RefreshCw, 
  CheckCircle, 
  AlertCircle, 
  Clock,
  MoreVertical,
  Search
} from 'lucide-react';
import toast from 'react-hot-toast';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn, formatFileSize, formatRelativeTime, formatNumber } from '@/lib/utils';
import { api } from '@/lib/api';
import type { FileMetadata } from '@/lib/types';

interface FileListProps {
  onFileSelect?: (fileId: string) => void;
  onFileDelete?: (fileId: string) => void;
  selectedFiles?: string[];
  className?: string;
  refreshTrigger?: number;
}

const FileList: React.FC<FileListProps> = ({
  onFileSelect,
  onFileDelete,
  selectedFiles = [],
  className,
  refreshTrigger = 0,
}) => {
  const [files, setFiles] = useState<FileMetadata[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  const loadFiles = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await api.files.getList(
        currentPage, 
        20, 
        statusFilter || undefined
      );
      
      setFiles(response.files);
      setTotalPages(Math.ceil(response.total / 20));
    } catch (err: any) {
      setError(err.message || 'Помилка завантаження файлів');
      toast.error('Не вдалося завантажити список файлів');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadFiles();
  }, [currentPage, statusFilter, refreshTrigger]);

  const handleDelete = async (fileId: string, filename: string) => {
    if (!confirm(`Ви впевнені, що хочете видалити файл "${filename}"?`)) {
      return;
    }

    try {
      await api.files.delete(fileId);
      toast.success('Файл успішно видалено');
      onFileDelete?.(fileId);
      loadFiles(); // Перезавантажуємо список
    } catch (err: any) {
      toast.error(`Помилка видалення файлу: ${err.message}`);
    }
  };

  const handleReindex = async (fileId: string, filename: string) => {
    try {
      await api.files.reindex(fileId);
      toast.success(`Індексація файлу "${filename}" розпочата`);
      loadFiles(); // Перезавантажуємо список
    } catch (err: any) {
      toast.error(`Помилка переіндексації: ${err.message}`);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      case 'indexing':
        return <RefreshCw className="w-4 h-4 text-blue-500 animate-spin" />;
      case 'uploaded':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      default:
        return <File className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Завершено';
      case 'error':
        return 'Помилка';
      case 'indexing':
        return 'Індексація';
      case 'uploaded':
        return 'Завантажено';
      case 'cancelled':
        return 'Скасовано';
      default:
        return 'Невідомо';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'text-green-600 bg-green-50';
      case 'error':
        return 'text-red-600 bg-red-50';
      case 'indexing':
        return 'text-blue-600 bg-blue-50';
      case 'uploaded':
        return 'text-yellow-600 bg-yellow-50';
      case 'cancelled':
        return 'text-gray-600 bg-gray-50';
      default:
        return 'text-gray-600 bg-gray-50';
    }
  };

  // Фільтрація файлів по пошуковому запиту
  const filteredFiles = files.filter(file =>
    file.original_filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading && files.length === 0) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="flex items-center justify-center">
            <RefreshCw className="w-6 h-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-muted-foreground">Завантаження файлів...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className}>
        <CardContent className="p-6">
          <div className="text-center">
            <AlertCircle className="w-12 h-12 text-red-500 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-red-600 mb-2">Помилка завантаження</h3>
            <p className="text-muted-foreground mb-4">{error}</p>
            <Button onClick={loadFiles} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Спробувати знову
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {/* Пошук та фільтри */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Пошук файлів..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
        </div>
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-3 py-2 border border-input rounded-md bg-background text-sm"
        >
          <option value="">Всі статуси</option>
          <option value="uploaded">Завантажено</option>
          <option value="indexing">Індексація</option>
          <option value="completed">Завершено</option>
          <option value="error">Помилка</option>
        </select>
        
        <Button onClick={loadFiles} variant="outline" size="sm">
          <RefreshCw className="w-4 h-4 mr-2" />
          Оновити
        </Button>
      </div>

      {/* Список файлів */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Файли ({filteredFiles.length})</span>
            {selectedFiles.length > 0 && (
              <span className="text-sm font-normal text-muted-foreground">
                Вибрано: {selectedFiles.length}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {filteredFiles.length === 0 ? (
            <div className="p-6 text-center text-muted-foreground">
              <File className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Файлів не знайдено</p>
              {searchQuery && (
                <p className="text-sm mt-2">
                  Спробуйте змінити критерії пошуку
                </p>
              )}
            </div>
          ) : (
            <div className="divide-y">
              {filteredFiles.map((file) => (
                <div
                  key={file.id}
                  className={cn(
                    'p-4 hover:bg-muted/50 transition-colors',
                    selectedFiles.includes(file.id) && 'bg-blue-50 border-l-4 border-blue-500'
                  )}
                >
                  <div className="flex items-center space-x-4">
                    {/* Чекбокс вибору */}
                    <input
                      type="checkbox"
                      checked={selectedFiles.includes(file.id)}
                      onChange={() => onFileSelect?.(file.id)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />

                    {/* Іконка файлу */}
                    <div className="flex-shrink-0">
                      <File className="w-8 h-8 text-blue-500" />
                    </div>

                    {/* Інформація про файл */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2">
                        <h3 className="text-sm font-medium truncate">
                          {file.original_filename}
                        </h3>
                        <div className={cn(
                          'inline-flex items-center px-2 py-1 rounded-full text-xs font-medium',
                          getStatusColor(file.status)
                        )}>
                          {getStatusIcon(file.status)}
                          <span className="ml-1">{getStatusText(file.status)}</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4 mt-1 text-xs text-muted-foreground">
                        <span>{formatFileSize(file.size)}</span>
                        <span>{formatRelativeTime(file.upload_date)}</span>
                        {file.status === 'completed' && file.entities_count && (
                          <>
                            <span>•</span>
                            <span>{formatNumber(file.entities_count)} сутностей</span>
                            <span>•</span>
                            <span>{formatNumber(file.relationships_count || 0)} зв'язків</span>
                          </>
                        )}
                      </div>

                      {file.error_message && (
                        <p className="text-xs text-red-600 mt-1">
                          {file.error_message}
                        </p>
                      )}
                    </div>

                    {/* Дії */}
                    <div className="flex items-center space-x-2">
                      {file.status === 'completed' && (
                        <Button size="sm" variant="ghost" title="Переглянути граф">
                          <Eye className="w-4 h-4" />
                        </Button>
                      )}
                      
                      {(file.status === 'error' || file.status === 'completed') && (
                        <Button 
                          size="sm" 
                          variant="ghost" 
                          onClick={() => handleReindex(file.id, file.original_filename)}
                          title="Переіндексувати"
                        >
                          <RefreshCw className="w-4 h-4" />
                        </Button>
                      )}
                      
                      <Button 
                        size="sm" 
                        variant="ghost" 
                        onClick={() => handleDelete(file.id, file.original_filename)}
                        title="Видалити"
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Пагінація */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Сторінка {currentPage} з {totalPages}
          </p>
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
            >
              Попередня
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
            >
              Наступна
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default FileList;
