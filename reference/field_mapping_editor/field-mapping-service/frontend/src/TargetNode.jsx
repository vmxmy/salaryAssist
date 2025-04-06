import React, { memo } from 'react';
import { Handle, Position, useNodes, useEdges } from 'reactflow';

// Use memo to prevent unnecessary re-renders if props haven't changed
const TargetNode = memo(({ id, data }) => {
  const nodes = useNodes();
  const edges = useEdges();

  // Calculate the display label inside the component
  let displayLabel = data.originalLabel; // Default

  if (data.calculationMode === 'manual') {
    if (data.manualExpression) {
      displayLabel = `${data.originalLabel} = ${data.manualExpression}`;
    }
  } else {
    // Auto mode: Calculate based on incoming connections
    const incomingEdges = edges.filter((edge) => edge.target === id);
    const sourceNodes = incomingEdges.map((edge) =>
      nodes.find((n) => n.id === edge.source)
    );
    const sourceLabels = sourceNodes
      .map((n) => n?.data?.originalLabel) // Use originalLabel from connected source nodes
      .filter(Boolean);

    let calculationString = '';
    if (sourceLabels.length === 1) {
      calculationString = sourceLabels[0];
    } else if (sourceLabels.length > 1) {
      calculationString = sourceLabels.join(' + ');
    }

    if (calculationString) {
      displayLabel = `${data.originalLabel} = ${calculationString}`;
    }
  }

  return (
    <div className="react-flow__node-default p-2 border border-gray-400 bg-white rounded min-w-[150px]">
      {/* Target handle on the left */}
      <Handle 
        type="target" 
        position={Position.Left} 
        id={`${id}-target`}
        className="!bg-teal-500"
      />
      {/* Display the calculated label */}
      <div className="text-center text-sm">
        {displayLabel}
      </div>
      {/* You could add source handle(s) if target nodes could also be sources */}
      {/* <Handle type="source" position={Position.Right} id={`${id}-source`} /> */}
    </div>
  );
});

export default TargetNode; 