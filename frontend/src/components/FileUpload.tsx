'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, X, File, AlertCircle, CheckCircle } from 'lucide-react';
import toast from 'react-hot-toast';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn, formatFileSize, isSupportedFileType } from '@/lib/utils';
import { api } from '@/lib/api';
import type { FileUploadResponse } from '@/lib/types';

interface FileUploadProps {
  onUploadComplete?: (response: FileUploadResponse) => void;
  onUploadStart?: (file: File) => void;
  className?: string;
  maxFiles?: number;
  disabled?: boolean;
}

interface UploadingFile {
  file: File;
  progress: number;
  status: 'uploading' | 'success' | 'error';
  response?: FileUploadResponse;
  error?: string;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onUploadComplete,
  onUploadStart,
  className,
  maxFiles = 5,
  disabled = false,
}) => {
  const [uploadingFiles, setUploadingFiles] = useState<UploadingFile[]>([]);
  const maxFileSize = parseInt(process.env.NEXT_PUBLIC_MAX_FILE_SIZE || '104857600'); // 100MB

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    if (disabled) return;

    // Фільтрація файлів
    const validFiles = acceptedFiles.filter(file => {
      // Перевірка типу файлу
      if (!isSupportedFileType(file.name)) {
        toast.error(`Файл ${file.name} має непідтримуваний тип`);
        return false;
      }

      // Перевірка розміру
      if (file.size > maxFileSize) {
        toast.error(`Файл ${file.name} завеликий. Максимальний розмір: ${formatFileSize(maxFileSize)}`);
        return false;
      }

      return true;
    });

    if (validFiles.length === 0) return;

    // Перевірка ліміту файлів
    if (uploadingFiles.length + validFiles.length > maxFiles) {
      toast.error(`Можна завантажити максимум ${maxFiles} файлів одночасно`);
      return;
    }

    // Ініціалізація файлів для завантаження
    const newUploadingFiles: UploadingFile[] = validFiles.map(file => ({
      file,
      progress: 0,
      status: 'uploading',
    }));

    setUploadingFiles(prev => [...prev, ...newUploadingFiles]);

    // Завантаження кожного файлу
    for (const uploadingFile of newUploadingFiles) {
      try {
        onUploadStart?.(uploadingFile.file);

        // Симуляція прогресу (у реальності можна використовувати onUploadProgress)
        const progressInterval = setInterval(() => {
          setUploadingFiles(prev => 
            prev.map(f => 
              f.file === uploadingFile.file && f.progress < 90
                ? { ...f, progress: f.progress + 10 }
                : f
            )
          );
        }, 200);

        const response = await api.files.upload(uploadingFile.file);

        clearInterval(progressInterval);

        setUploadingFiles(prev =>
          prev.map(f =>
            f.file === uploadingFile.file
              ? { ...f, progress: 100, status: 'success', response }
              : f
          )
        );

        onUploadComplete?.(response);
        toast.success(`Файл ${uploadingFile.file.name} успішно завантажено`);

      } catch (error: any) {
        setUploadingFiles(prev =>
          prev.map(f =>
            f.file === uploadingFile.file
              ? { 
                  ...f, 
                  progress: 0, 
                  status: 'error', 
                  error: error.message || 'Помилка завантаження'
                }
              : f
          )
        );

        toast.error(`Помилка завантаження ${uploadingFile.file.name}: ${error.message}`);
      }
    }
  }, [disabled, maxFiles, maxFileSize, uploadingFiles.length, onUploadStart, onUploadComplete]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    disabled,
    maxFiles,
    maxSize: maxFileSize,
    accept: {
      'text/plain': ['.txt'],
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/msword': ['.doc'],
    },
  });

  const removeFile = (fileToRemove: File) => {
    setUploadingFiles(prev => prev.filter(f => f.file !== fileToRemove));
  };

  const retryUpload = async (uploadingFile: UploadingFile) => {
    if (uploadingFile.status !== 'error') return;

    setUploadingFiles(prev =>
      prev.map(f =>
        f.file === uploadingFile.file
          ? { ...f, status: 'uploading', progress: 0, error: undefined }
          : f
      )
    );

    try {
      const response = await api.files.upload(uploadingFile.file);
      
      setUploadingFiles(prev =>
        prev.map(f =>
          f.file === uploadingFile.file
            ? { ...f, progress: 100, status: 'success', response }
            : f
        )
      );

      onUploadComplete?.(response);
      toast.success(`Файл ${uploadingFile.file.name} успішно завантажено`);
    } catch (error: any) {
      setUploadingFiles(prev =>
        prev.map(f =>
          f.file === uploadingFile.file
            ? { ...f, status: 'error', error: error.message }
            : f
        )
      );
      toast.error(`Помилка завантаження: ${error.message}`);
    }
  };

  return (
    <div className={cn('space-y-4', className)}>
      {/* Dropzone */}
      <Card 
        {...getRootProps()} 
        className={cn(
          'cursor-pointer border-2 border-dashed transition-colors',
          isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25',
          disabled && 'cursor-not-allowed opacity-50'
        )}
      >
        <CardHeader className="text-center">
          <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center mb-4">
            <Upload className="w-6 h-6 text-primary" />
          </div>
          <CardTitle className="text-lg">
            {isDragActive ? 'Відпустіть файли тут' : 'Завантажити файли'}
          </CardTitle>
          <p className="text-sm text-muted-foreground">
            Перетягніть файли сюди або клікніть для вибору
          </p>
          <p className="text-xs text-muted-foreground">
            Підтримуються: TXT, PDF, DOCX (до {formatFileSize(maxFileSize)})
          </p>
        </CardHeader>
        <input {...getInputProps()} />
      </Card>

      {/* Список файлів що завантажуються */}
      {uploadingFiles.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Завантаження файлів</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {uploadingFiles.map((uploadingFile, index) => (
              <div
                key={`${uploadingFile.file.name}-${index}`}
                className="flex items-center space-x-3 p-3 border rounded-lg"
              >
                <File className="w-8 h-8 text-blue-500 flex-shrink-0" />
                
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">
                    {uploadingFile.file.name}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatFileSize(uploadingFile.file.size)}
                  </p>
                  
                  {uploadingFile.status === 'uploading' && (
                    <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                      <div
                        className="bg-primary h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadingFile.progress}%` }}
                      />
                    </div>
                  )}
                  
                  {uploadingFile.status === 'error' && uploadingFile.error && (
                    <p className="text-xs text-red-500 mt-1">
                      {uploadingFile.error}
                    </p>
                  )}
                </div>

                <div className="flex items-center space-x-2">
                  {uploadingFile.status === 'uploading' && (
                    <div className="animate-spin w-4 h-4 border-2 border-primary border-t-transparent rounded-full" />
                  )}
                  
                  {uploadingFile.status === 'success' && (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  )}
                  
                  {uploadingFile.status === 'error' && (
                    <div className="flex space-x-1">
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => retryUpload(uploadingFile)}
                      >
                        Повторити
                      </Button>
                      <AlertCircle className="w-5 h-5 text-red-500" />
                    </div>
                  )}
                  
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      removeFile(uploadingFile.file);
                    }}
                  >
                    <X className="w-4 h-4" />
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default FileUpload;
