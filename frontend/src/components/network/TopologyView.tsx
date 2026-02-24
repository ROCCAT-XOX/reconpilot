import { useMemo } from 'react'
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  ConnectionMode,
} from 'reactflow'
import 'reactflow/dist/style.css'

interface Host {
  ip: string
  hostname?: string
  ports: number[]
  os?: string
}

interface Props {
  hosts: Host[]
}

function buildGraph(hosts: Host[]): { nodes: Node[]; edges: Edge[] } {
  const gatewayNode: Node = {
    id: 'gateway',
    position: { x: 400, y: 50 },
    data: { label: '🌐 Target Network' },
    style: { background: '#1e293b', color: '#94a3b8', border: '1px solid #475569', borderRadius: 8, padding: 10, fontSize: 12 },
  }

  const nodes: Node[] = [gatewayNode]
  const edges: Edge[] = []

  hosts.forEach((host, i) => {
    const id = `host-${i}`
    const cols = 4
    const x = (i % cols) * 220 + 100
    const y = Math.floor(i / cols) * 150 + 200

    const portList = host.ports.slice(0, 5).join(', ')
    const extra = host.ports.length > 5 ? ` +${host.ports.length - 5}` : ''

    nodes.push({
      id,
      position: { x, y },
      data: {
        label: (
          <div className="text-left">
            <div className="font-bold text-xs">{host.hostname || host.ip}</div>
            {host.hostname && <div className="text-[10px] text-gray-400">{host.ip}</div>}
            <div className="text-[10px] text-gray-500 mt-1">Ports: {portList}{extra}</div>
            {host.os && <div className="text-[10px] text-blue-400">{host.os}</div>}
          </div>
        ),
      },
      style: {
        background: '#0f172a',
        color: '#e2e8f0',
        border: '1px solid #334155',
        borderRadius: 8,
        padding: 8,
        width: 180,
      },
    })

    edges.push({
      id: `e-gw-${id}`,
      source: 'gateway',
      target: id,
      style: { stroke: '#475569' },
      animated: true,
    })
  })

  return { nodes, edges }
}

export default function TopologyView({ hosts }: Props) {
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => buildGraph(hosts), [hosts])
  const [nodes, , onNodesChange] = useNodesState(initialNodes)
  const [edges, , onEdgesChange] = useEdgesState(initialEdges)

  if (hosts.length === 0) {
    return (
      <div className="flex items-center justify-center h-96 bg-dark-900 rounded-xl border border-dark-700">
        <p className="text-gray-500 text-sm">No hosts discovered yet. Run a scan to populate the topology view.</p>
      </div>
    )
  }

  return (
    <div className="h-[500px] bg-dark-950 rounded-xl border border-dark-700 overflow-hidden">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectionMode={ConnectionMode.Loose}
        fitView
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#1e293b" gap={20} />
        <Controls className="!bg-dark-800 !border-dark-600 !shadow-lg [&>button]:!bg-dark-700 [&>button]:!border-dark-600 [&>button]:!text-gray-300" />
        <MiniMap
          nodeColor="#334155"
          maskColor="rgba(0,0,0,0.6)"
          style={{ background: '#0f172a', borderRadius: 8 }}
        />
      </ReactFlow>
    </div>
  )
}
