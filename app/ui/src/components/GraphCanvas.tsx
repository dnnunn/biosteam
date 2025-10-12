"use client";
import React, { useCallback } from 'react';
import ReactFlow, { Background, Controls, MiniMap, addEdge, Connection, Edge, Node } from 'reactflow';
import 'reactflow/dist/style.css';
import { useGraphStore } from '@/state/graphStore';

export function GraphCanvas() {
  const { nodes, edges, setNodes, setEdges } = useGraphStore();

  const onNodesChange = useCallback((changes: any) => setNodes(changes), [setNodes]);
  const onEdgesChange = useCallback((changes: any) => setEdges(changes), [setEdges]);
  const onConnect = useCallback((params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

  return (
    <ReactFlow nodes={nodes as Node[]} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} fitView>
      <MiniMap />
      <Controls />
      <Background gap={16} color="#f3f3f3" />
    </ReactFlow>
  );
}

