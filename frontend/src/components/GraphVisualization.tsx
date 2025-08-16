'use client';

import React, { useEffect, useRef, useState, useCallback } from 'react';
import cytoscape, { Core, EdgeSingular, NodeSingular } from 'cytoscape';
import coseBilkent from 'cytoscape-cose-bilkent';
import cola from 'cytoscape-cola';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize, 
  Download, 
  Settings, 
  Filter,
  Search,
  Info,
  RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { cn, generateRandomColor, downloadAsFile } from '@/lib/utils';
import { api } from '@/lib/api';
import type { GraphData, Entity, Relationship, CytoscapeElement } from '@/lib/types';

// Регистрация расширений Cytoscape
if (typeof cytoscape !== 'undefined') {
  cytoscape.use(coseBilkent);
  cytoscape.use(cola);
}

interface GraphVisualizationProps {
  fileIds: string[];
  className?: string;
  height?: string;
  onNodeSelect?: (nodeId: string, nodeData: any) => void;
  onEdgeSelect?: (edgeId: string, edgeData: any) => void;
}

interface GraphSettings {
  layout: 'cose-bilkent' | 'cola' | 'circle' | 'grid';
  showLabels: boolean;
  showCommunities: boolean;
  nodeSize: 'degree' | 'fixed';
  edgeWeight: boolean;
  filterMinDegree: number;
  colorBy: 'type' | 'community' | 'degree';
}

const GraphVisualization: React.FC<GraphVisualizationProps> = ({
  fileIds,
  className,
  height = '600px',
  onNodeSelect,
  onEdgeSelect,
}) => {
  const cyRef = useRef<HTMLDivElement>(null);
  const cyInstance = useRef<Core | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [selectedEdge, setSelectedEdge] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSettings, setShowSettings] = useState(false);
  const [settings, setSettings] = useState<GraphSettings>({
    layout: 'cose-bilkent',
    showLabels: true,
    showCommunities: true,
    nodeSize: 'degree',
    edgeWeight: true,
    filterMinDegree: 0,
    colorBy: 'type',
  });

  // Цветовая схема для типов узлов
  const nodeColors = {
    person: '#3B82F6',
    organization: '#EF4444',
    location: '#10B981',
    concept: '#F59E0B',
    event: '#8B5CF6',
    technology: '#06B6D4',
    default: '#6B7280',
  };

  // Загрузка данных графа
  const loadGraphData = useCallback(async () => {
    if (fileIds.length === 0) {
      setGraphData(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await api.graph.getData(fileIds, false);
      setGraphData(data);
    } catch (err: any) {
      setError(err.message || 'Ошибка загрузки данных графа');
      toast.error('Не удалось загрузить граф');
    } finally {
      setLoading(false);
    }
  }, [fileIds]);

  // Преобразование данных для Cytoscape
  const convertToCytoscapeFormat = useCallback((data: GraphData): CytoscapeElement => {
    const nodes = data.entities
      .filter(entity => entity.degree >= settings.filterMinDegree)
      .map(entity => {
        let color = nodeColors.default;
        
        if (settings.colorBy === 'type') {
          color = nodeColors[entity.type as keyof typeof nodeColors] || nodeColors.default;
        } else if (settings.colorBy === 'community' && entity.community_id) {
          color = generateRandomColor();
        } else if (settings.colorBy === 'degree') {
          const intensity = Math.min(entity.degree / 10, 1);
          color = `rgba(59, 130, 246, ${0.5 + intensity * 0.5})`;
        }

        let size = 30;
        if (settings.nodeSize === 'degree') {
          size = Math.max(20, Math.min(80, 20 + entity.degree * 3));
        }

        return {
          data: {
            id: entity.id,
            label: entity.name,
            type: entity.type,
            description: entity.description || '',
            degree: entity.degree,
            community: entity.community_id,
          },
          position: entity.x && entity.y ? { x: entity.x, y: entity.y } : undefined,
          style: {
            'background-color': color,
            'width': size,
            'height': size,
            'label': settings.showLabels ? entity.name : '',
            'font-size': '12px',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#333',
            'text-outline-color': '#fff',
            'text-outline-width': 2,
          },
        };
      });

    const entityIds = new Set(nodes.map(n => n.data.id));
    const edges = data.relationships
      .filter(rel => entityIds.has(rel.source_id) && entityIds.has(rel.target_id))
      .map(rel => ({
        data: {
          id: rel.id,
          source: rel.source_id,
          target: rel.target_id,
          label: rel.relationship_type,
          weight: rel.weight,
          type: rel.relationship_type,
        },
        style: {
          'width': settings.edgeWeight ? Math.max(1, rel.weight * 3) : 2,
          'line-color': '#ccc',
          'target-arrow-color': '#ccc',
          'target-arrow-shape': 'triangle',
          'curve-style': 'bezier',
          'label': settings.showLabels ? rel.relationship_type : '',
          'font-size': '10px',
          'color': '#666',
          'text-rotation': 'autorotate',
        },
      }));

    return { nodes, edges };
  }, [settings]);

  // Инициализация Cytoscape
  const initializeCytoscape = useCallback(() => {
    if (!cyRef.current || !graphData) return;

    // Удаление предыдущего экземпляра
    if (cyInstance.current) {
      cyInstance.current.destroy();
    }

    const cytoscapeData = convertToCytoscapeFormat(graphData);
    
    cyInstance.current = cytoscape({
      container: cyRef.current,
      elements: [...cytoscapeData.nodes, ...cytoscapeData.edges],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)',
            'label': 'data(label)',
            'width': 'data(size)',
            'height': 'data(size)',
            'font-size': '12px',
            'text-valign': 'center',
            'text-halign': 'center',
            'color': '#333',
            'text-outline-color': '#fff',
            'text-outline-width': 2,
          },
        },
        {
          selector: 'edge',
          style: {
            'width': 'data(width)',
            'line-color': '#ccc',
            'target-arrow-color': '#ccc',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'label': 'data(label)',
            'font-size': '10px',
            'color': '#666',
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 3,
            'border-color': '#3B82F6',
            'border-opacity': 1,
          },
        },
        {
          selector: 'edge:selected',
          style: {
            'line-color': '#3B82F6',
            'target-arrow-color': '#3B82F6',
            'width': 4,
          },
        },
      ],
      layout: {
        name: settings.layout,
        animate: true,
        animationDuration: 500,
        fit: true,
        padding: 50,
        // Дополнительные параметры для разных алгоритмов
        ...(settings.layout === 'cose-bilkent' && {
          idealEdgeLength: 100,
          nodeOverlap: 20,
          refresh: 30,
          randomize: false,
        }),
        ...(settings.layout === 'cola' && {
          animate: true,
          refresh: 1,
          maxSimulationTime: 4000,
          ungrabifyWhileSimulating: false,
          fit: true,
          padding: 30,
          nodeDimensionsIncludeLabels: false,
        }),
      },
      minZoom: 0.1,
      maxZoom: 3,
      wheelSensitivity: 0.2,
    });

    // События
    cyInstance.current.on('tap', 'node', (event) => {
      const node = event.target;
      const nodeData = node.data();
      setSelectedNode(nodeData);
      setSelectedEdge(null);
      onNodeSelect?.(nodeData.id, nodeData);
    });

    cyInstance.current.on('tap', 'edge', (event) => {
      const edge = event.target;
      const edgeData = edge.data();
      setSelectedEdge(edgeData);
      setSelectedNode(null);
      onEdgeSelect?.(edgeData.id, edgeData);
    });

    cyInstance.current.on('tap', (event) => {
      if (event.target === cyInstance.current) {
        setSelectedNode(null);
        setSelectedEdge(null);
      }
    });

  }, [graphData, settings, convertToCytoscapeFormat, onNodeSelect, onEdgeSelect]);

  // Эффекты
  useEffect(() => {
    loadGraphData();
  }, [loadGraphData]);

  useEffect(() => {
    if (graphData) {
      initializeCytoscape();
    }
  }, [graphData, initializeCytoscape]);

  // Управление графом
  const handleZoomIn = () => {
    cyInstance.current?.zoom(cyInstance.current.zoom() * 1.2);
    cyInstance.current?.center();
  };

  const handleZoomOut = () => {
    cyInstance.current?.zoom(cyInstance.current.zoom() * 0.8);
    cyInstance.current?.center();
  };

  const handleFit = () => {
    cyInstance.current?.fit();
  };

  const handleSearch = () => {
    if (!cyInstance.current || !searchQuery.trim()) return;

    // Сброс предыдущего поиска
    cyInstance.current.elements().removeClass('highlighted');

    // Поиск узлов
    const query = searchQuery.toLowerCase();
    const matchingNodes = cyInstance.current.nodes().filter(node => {
      const data = node.data();
      return (
        data.label.toLowerCase().includes(query) ||
        data.type.toLowerCase().includes(query) ||
        data.description.toLowerCase().includes(query)
      );
    });

    if (matchingNodes.length > 0) {
      // Подсветка найденных узлов
      matchingNodes.addClass('highlighted');
      
      // Фокус на первом найденном узле
      cyInstance.current.animate({
        fit: {
          eles: matchingNodes,
          padding: 50,
        },
        duration: 500,
      });

      toast.success(`Найдено ${matchingNodes.length} узлов`);
    } else {
      toast.error('Узлы не найдены');
    }
  };

  const handleExport = () => {
    if (!cyInstance.current) return;

    const png = cyInstance.current.png({
      output: 'blob',
      bg: 'white',
      full: true,
      scale: 2,
    });

    const link = document.createElement('a');
    link.href = URL.createObjectURL(png);
    link.download = `graph-${Date.now()}.png`;
    link.click();

    toast.success('Граф экспортирован');
  };

  const handleLayoutChange = (newLayout: GraphSettings['layout']) => {
    setSettings(prev => ({ ...prev, layout: newLayout }));
    if (cyInstance.current) {
      cyInstance.current.layout({ name: newLayout, animate: true }).run();
    }
  };

  if (loading) {
    return (
      <Card className={className} style={{ height }}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <RefreshCw className="w-8 h-8 animate-spin text-muted-foreground mx-auto mb-4" />
            <p className="text-muted-foreground">Загрузка графа...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className={className} style={{ height }}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center">
            <p className="text-red-600 mb-4">{error}</p>
            <Button onClick={loadGraphData} variant="outline">
              <RefreshCw className="w-4 h-4 mr-2" />
              Повторить
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!graphData || fileIds.length === 0) {
    return (
      <Card className={className} style={{ height }}>
        <CardContent className="flex items-center justify-center h-full">
          <div className="text-center text-muted-foreground">
            <p>Выберите файлы для отображения графа</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className={cn('flex flex-col', className)} style={{ height }}>
      {/* Панель управления */}
      <div className="flex items-center justify-between p-4 border-b bg-muted/50">
        <div className="flex items-center space-x-2">
          <div className="flex items-center space-x-1 border rounded-md overflow-hidden">
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomIn}
              className="rounded-none"
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleZoomOut}
              className="rounded-none"
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleFit}
              className="rounded-none"
            >
              <Maximize className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex items-center space-x-2">
            <Input
              placeholder="Поиск узлов..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              className="w-48"
            />
            <Button size="sm" onClick={handleSearch}>
              <Search className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <select
            value={settings.layout}
            onChange={(e) => handleLayoutChange(e.target.value as GraphSettings['layout'])}
            className="px-3 py-1 border rounded-md text-sm"
          >
            <option value="cose-bilkent">Cose-Bilkent</option>
            <option value="cola">Cola</option>
            <option value="circle">Circular</option>
            <option value="grid">Grid</option>
          </select>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowSettings(!showSettings)}
          >
            <Settings className="w-4 h-4" />
          </Button>

          <Button variant="ghost" size="sm" onClick={handleExport}>
            <Download className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Настройки */}
      {showSettings && (
        <div className="p-4 border-b bg-muted/30">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.showLabels}
                onChange={(e) => setSettings(prev => ({ ...prev, showLabels: e.target.checked }))}
              />
              <span className="text-sm">Показать метки</span>
            </label>

            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={settings.edgeWeight}
                onChange={(e) => setSettings(prev => ({ ...prev, edgeWeight: e.target.checked }))}
              />
              <span className="text-sm">Вес ребер</span>
            </label>

            <div className="flex items-center space-x-2">
              <span className="text-sm">Размер узлов:</span>
              <select
                value={settings.nodeSize}
                onChange={(e) => setSettings(prev => ({ ...prev, nodeSize: e.target.value as any }))}
                className="px-2 py-1 border rounded text-sm"
              >
                <option value="fixed">Фиксированный</option>
                <option value="degree">По степени</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm">Цвет по:</span>
              <select
                value={settings.colorBy}
                onChange={(e) => setSettings(prev => ({ ...prev, colorBy: e.target.value as any }))}
                className="px-2 py-1 border rounded text-sm"
              >
                <option value="type">Типу</option>
                <option value="community">Сообществу</option>
                <option value="degree">Степени</option>
              </select>
            </div>
          </div>
        </div>
      )}

      {/* Основная область графа */}
      <div className="flex-1 relative">
        <div ref={cyRef} className="w-full h-full" />
        
        {/* Информационная панель */}
        {(selectedNode || selectedEdge) && (
          <div className="absolute top-4 right-4 w-80 bg-white border shadow-lg rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="font-semibold flex items-center">
                <Info className="w-4 h-4 mr-2" />
                {selectedNode ? 'Информация об узле' : 'Информация о ребре'}
              </h4>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  setSelectedNode(null);
                  setSelectedEdge(null);
                }}
              >
                ×
              </Button>
            </div>

            {selectedNode && (
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Название:</span>
                  <p className="text-sm">{selectedNode.label}</p>
                </div>
                <div>
                  <span className="font-medium">Тип:</span>
                  <p className="text-sm capitalize">{selectedNode.type}</p>
                </div>
                <div>
                  <span className="font-medium">Степень:</span>
                  <p className="text-sm">{selectedNode.degree}</p>
                </div>
                {selectedNode.description && (
                  <div>
                    <span className="font-medium">Описание:</span>
                    <p className="text-sm">{selectedNode.description}</p>
                  </div>
                )}
              </div>
            )}

            {selectedEdge && (
              <div className="space-y-2">
                <div>
                  <span className="font-medium">Тип связи:</span>
                  <p className="text-sm">{selectedEdge.label}</p>
                </div>
                <div>
                  <span className="font-medium">Вес:</span>
                  <p className="text-sm">{selectedEdge.weight}</p>
                </div>
                <div>
                  <span className="font-medium">От:</span>
                  <p className="text-sm">{selectedEdge.source}</p>
                </div>
                <div>
                  <span className="font-medium">К:</span>
                  <p className="text-sm">{selectedEdge.target}</p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Статистика */}
        <div className="absolute bottom-4 left-4 bg-white border shadow-lg rounded-lg p-3">
          <div className="text-xs space-y-1">
            <div>Узлов: {graphData.entities.length}</div>
            <div>Ребер: {graphData.relationships.length}</div>
            <div>Сообществ: {graphData.communities.length}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GraphVisualization;
