// react-flow 替代拖拽表达式构建器
import React, { useState, useCallback, useEffect, useRef } from 'react';
import ReactFlow, {
  ReactFlowProvider,
  addEdge,
  Background,
  MiniMap,
  Controls,
  useNodesState,
  useEdgesState,
  Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import * as XLSX from 'xlsx';
import dagre from 'dagre'; // Import dagre
import ExpressionEditorModal from './ExpressionEditorModal'; // Import the modal component
import TargetNode from './TargetNode'; // Import the custom node component

const initialNodes = [];
const initialEdges = [];

// Define nodeTypes outside the component to prevent recreation on renders
const nodeTypes = { target: TargetNode };

// Helper function to generate unique IDs (basic example)
let idCounter = 0;
const generateUniqueId = (prefix) => `${prefix}-${Date.now()}-${idCounter++}`;

// --- Dagre Layout Function ---
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const nodeWidth = 172; // Adjust as needed based on your node styling
const nodeHeight = 36; // Adjust as needed

const getLayoutedElements = (nodes, edges, direction = 'LR') => {
  dagreGraph.setGraph({ rankdir: direction, ranksep: 100, nodesep: 50 });

  // --- Sorting Logic --- 
  const sourceNodes = [];
  const targetNodes = [];
  nodes.forEach(node => {
      if (node.id.startsWith('src-')) {
          sourceNodes.push(node);
      } else if (node.id.startsWith('tgt-')) {
          targetNodes.push(node);
      } else {
          // Handle potential other node types if necessary
          console.warn("Encountered node with unknown type for sorting:", node);
          // Decide how to handle them - maybe put in a separate list or log
      }
  });

  // Sort each group alphabetically by originalLabel
  sourceNodes.sort((a, b) => (a.data.originalLabel || '').localeCompare(b.data.originalLabel || ''));
  targetNodes.sort((a, b) => (a.data.originalLabel || '').localeCompare(b.data.originalLabel || ''));

  // Combine sorted lists - layout will respect this order within ranks
  const sortedNodes = [...sourceNodes, ...targetNodes];
  // --- End Sorting Logic ---

  // Use sortedNodes for adding to Dagre and applying layout
  sortedNodes.forEach((node) => {
    // Check prevents error if layout is called multiple times
    // Use the actual node width/height if available, otherwise default
    const width = node.width || nodeWidth;
    const height = node.height || nodeHeight;
    if (!dagreGraph.hasNode(node.id)) { 
        dagreGraph.setNode(node.id, { width, height }); // Use potentially dynamic width/height
    }
  });

  edges.forEach((edge) => {
    if (!dagreGraph.hasEdge(edge.source, edge.target)) {
        dagreGraph.setEdge(edge.source, edge.target);
    }
  });

  dagre.layout(dagreGraph);

  // Apply positions based on the sortedNodes order
  const layoutedNodes = sortedNodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    if (nodeWithPosition) {
        // Adjust for node anchor point difference (Dagre center vs React Flow top-left)
        // Use the actual width/height used in layout calculation
         const width = node.width || nodeWidth;
         const height = node.height || nodeHeight;
        node.position = {
            x: nodeWithPosition.x - width / 2,
            y: nodeWithPosition.y - height / 2,
        };
    }
    return node;
  });

  return { nodes: layoutedNodes, edges }; 
};

// --- NEW: Helper function to transform raw mapping data ---
const transformRawMappings = (rawMappings) => {
  if (!Array.isArray(rawMappings)) return []; // Ensure input is an array

  return rawMappings.map((rawMapping, index) => {
    if (typeof rawMapping !== 'object' || rawMapping === null) {
      console.warn(`Skipping invalid mapping entry at index ${index} (not an object):`, rawMapping);
      return null;
    }

    const newMapping = {};

    // Target field (prioritize target_field, fallback to target)
    newMapping.target = rawMapping.target_field || rawMapping.target;

    // Source fields (handle source_fields array, source_field string, or neither)
    if (Array.isArray(rawMapping.source_fields)) {
      newMapping.source_fields = rawMapping.source_fields;
    } else if (typeof rawMapping.source_field === 'string') {
      newMapping.source_fields = [rawMapping.source_field];
    } else {
      newMapping.source_fields = []; // Default to empty array
    }

    // Calculation (optional)
    if (rawMapping.calculation !== undefined) {
      newMapping.calculation = rawMapping.calculation;
    }

    // --- Validation of the transformed structure ---
    if (typeof newMapping.target !== 'string' || newMapping.target.trim() === '' || !Array.isArray(newMapping.source_fields)) {
      console.warn(`Skipping mapping entry at index ${index} due to invalid structure after transformation (missing/invalid target or source_fields):`, rawMapping, newMapping);
      return null; // Skip invalid ones
    }
    // Further validation: ensure all source_fields are strings
    if (!newMapping.source_fields.every(sf => typeof sf === 'string')) {
        console.warn(`Skipping mapping entry at index ${index} due to non-string value within source_fields:`, rawMapping, newMapping);
        return null;
    }


    return newMapping;
  }).filter(Boolean); // Remove nulls from skipped mappings
};

export default function FieldMappingFlow() {
  const [sources, setSources] = useState([]);
  const [targets, setTargets] = useState([]);
  const [sourceRow, setSourceRow] = useState(2); // Default to 3rd row (index 2)
  const [targetRow, setTargetRow] = useState(2); // Default to 3rd row (index 2)
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // State for the modal
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingNodeId, setEditingNodeId] = useState(null);
  const [modalInitialExpression, setModalInitialExpression] = useState('');

  // State for click-to-connect
  const [selectedSourceNodeId, setSelectedSourceNodeId] = useState(null);
  // Add loading state for file processing
  const [isLoadingSource, setIsLoadingSource] = useState(false);
  const [isLoadingTarget, setIsLoadingTarget] = useState(false); // Add loading for target
  const [isLoadingMappings, setIsLoadingMappings] = useState(false); // Add loading for mapping import

  // Ref for the import file input
  const importMappingInputRef = useRef(null);

  const onConnect = useCallback(
    (params) => {
       // Prevent self-connections or tgt-to-tgt / src-to-src connections visually
       const sourceIsTarget = params.sourceHandle?.startsWith('tgt-'); // Heuristic check
       const targetIsSource = params.targetHandle?.startsWith('src-'); // Heuristic check
       if (params.source === params.target || sourceIsTarget || targetIsSource) {
           console.warn("Prevented invalid connection");
           return; // Don't add the edge
       }
       setEdges((eds) => addEdge({ ...params, animated: true }, eds));
     },
    [setEdges]
  );

  // Helper function to calculate the automatic expression string (remains mostly the same)
  // Modified slightly to accept nodes/edges directly if needed, or use current state
  const calculateAutoExpressionInternal = useCallback((targetNodeId, currentNodes, currentEdges) => {
      const incomingEdges = currentEdges.filter((edge) => edge.target === targetNodeId);
      const sourceNodes = incomingEdges
          .map((edge) => currentNodes.find((n) => n.id === edge.source))
          .filter(Boolean); // Filter out undefined if a source node wasn't found (shouldn't happen in normal flow)

      const sourceLabels = sourceNodes
        .map((n) => n?.data?.originalLabel)
        .filter(Boolean);

      if (sourceLabels.length === 1) {
        return sourceLabels[0];
      } else if (sourceLabels.length > 1) {
        // Sort labels alphabetically for consistent auto-expressions regardless of connection order
        return sourceLabels.sort().join(' + ');
      }
      return ''; // Return empty if no connections
  }, []);

  // --- Function to process multiple source files ---
  const processSourceFiles = async (fileList) => {
    if (!fileList || fileList.length === 0) return;
    setIsLoadingSource(true);
    let currentNodes = nodes; // Get snapshot
    let allNewSourceNodes = [];
    let allSourceFieldsInfo = []; // Keep track of file info
    
    // --- Setup for processing (colors, existing nodes map) ---
    const baseSourceX = -300; // No longer needed for manual layout
    const sourceColSpacing = 250; // No longer needed
    const sourceRowSpacing = 60; // No longer needed
    const sourceColors = ['#e0f2fe', '#dcfce7', '#fef9c3', '#ffe4e6', '#f3e8ff', '#fae8ff', '#dbeafe', '#e0e7ff'];
    const fileColorMap = {};
    const existingSourceNodesMap = new Map(
      currentNodes.filter(n => n.id.startsWith('src-')).map(n => [n.data.originalLabel, n])
    );
    let sourceFileCount = currentNodes.reduce((acc, node) => {
        if (node.data.sourceFile && node.data.sourceFile !== 'imported' && !acc.has(node.data.sourceFile)) {
            acc.add(node.data.sourceFile);
        }
        return acc;
    }, new Set()).size;

    const fileArray = Array.from(fileList);

    for (let fileIndex = 0; fileIndex < fileArray.length; fileIndex++) {
      const file = fileArray[fileIndex];
      const effectiveFileIndex = sourceFileCount + fileIndex;
      
      try {
        // Assign color
        if (!fileColorMap[file.name]) {
             fileColorMap[file.name] = sourceColors[effectiveFileIndex % sourceColors.length];
        }
        const backgroundColor = fileColorMap[file.name];

        // --- Read File Headers ---
        const fileHeaders = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                try {
                    const data = new Uint8Array(e.target.result);
                    const workbook = XLSX.read(data, { type: 'array' });
                    const sheetName = workbook.SheetNames[0];
                    const worksheet = workbook.Sheets[sheetName];
                    const json = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' });
                    if (sourceRow < 0 || sourceRow >= json.length) {
                        return reject(new Error(`文件 "${file.name}" 行号 (${sourceRow + 1}) 无效。`));
                    }
                    const headers = (json[sourceRow] || []).map(h => String(h).trim()).filter(Boolean);
                    if (headers.length === 0) console.warn(`文件 "${file.name}" 第 ${sourceRow + 1} 行未找到字段。`);
                    resolve(headers);
                } catch (parseError) {
                    reject(new Error(`解析 "${file.name}" 出错: ${parseError.message}`));
                }
            };
            reader.onerror = (error) => reject(new Error(`读取 "${file.name}" 失败: ${error.message}`));
            reader.readAsArrayBuffer(file);
        });
        // --- End Read File Headers ---

        if (fileHeaders && fileHeaders.length > 0) {
            allSourceFieldsInfo.push({ fileName: file.name, headers: fileHeaders });

            fileHeaders.forEach((name) => {
                // Check if a node with this label already exists
                if (!existingSourceNodesMap.has(name)) {
                    const nodeId = generateUniqueId(`src-${file.name}`);
                    const nodeData = {
                        label: name,
                        originalLabel: name,
                        sourceFile: file.name
                    };
                    // Position will be set by Dagre, remove manual calculation
                    const newNode = {
                        id: nodeId,
                        data: nodeData,
                        position: { x: 0, y: 0 }, // Initial dummy position
                        style: { backgroundColor: backgroundColor, width: 'auto', minWidth: '150px' },
                        sourcePosition: Position.Right,
                        targetPosition: undefined,
                        type: 'default',
                    };
                    allNewSourceNodes.push(newNode);
                    existingSourceNodesMap.set(name, newNode); // Track newly added
                } else {
                     console.log(`Source field "${name}" from file "${file.name}" already exists.`);
                     // Optional: Update style/sourceFile of existing node?
                     // For now, we just skip creating a duplicate.
                }
            });
        }
      } catch (error) {
        console.error(error);
        alert(error.message);
      }
    } // End loop through files

    // --- Update State and Trigger Layout ---
    setSources(prevSources => [...prevSources, ...allSourceFieldsInfo]); 
    if (allNewSourceNodes.length > 0) {
      const finalNodes = [
        ...currentNodes, 
        ...allNewSourceNodes
      ];
      // Get current edges (no edges added here)
      const currentEdges = edges;
      // Calculate layout
      const { nodes: layoutedNodes } = getLayoutedElements(finalNodes, currentEdges);
      // Update state with layouted nodes
      setNodes(layoutedNodes);
    }
    setIsLoadingSource(false);
  };


  // --- Updated function for target file (using isLoadingTarget) ---
  const readExcelHeadersTarget = (file) => {
    if (!file) return;
    setIsLoadingTarget(true);
    const reader = new FileReader();
    reader.onload = (e) => {
      let newTargetNodes = []; // Collect new nodes
      try {
        // --- Read Excel --- 
        const data = new Uint8Array(e.target.result);
        const workbook = XLSX.read(data, { type: 'array' });
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const json = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' });
        const headerRowIndex = targetRow;

        if (headerRowIndex < 0 || headerRowIndex >= json.length) {
          throw new Error(`目标文件行号 (${headerRowIndex + 1}) 无效。`);
        }
        const headers = json[headerRowIndex] || [];
        const fieldList = headers.map(h => String(h).trim()).filter(Boolean);
        if (fieldList.length === 0) {
           console.warn(`目标文件第 ${headerRowIndex + 1} 行未找到有效字段名。`);
        }
        // --- End Read Excel ---

        // --- Node Creation Logic (only create new) ---
         let currentNodes = nodes; // Snapshot
         const existingTargetNodesMap = new Map(
             currentNodes.filter(n => n.id.startsWith('tgt-')).map(n => [n.data.originalLabel, n])
         );
         
        fieldList.forEach((name) => {
            if (!existingTargetNodesMap.has(name)) {
                const nodeData = {
                  originalLabel: name,
                  calculationMode: 'auto',
                  manualExpression: ''
                };
                const nodeId = generateUniqueId('tgt');
                // Remove manual position calculation
                const newNode = {
                    id: nodeId,
                    data: nodeData,
                    position: { x: 0, y: 0 }, // Dummy position
                    sourcePosition: undefined,
                    targetPosition: Position.Left,
                    type: 'target',
                };
                newTargetNodes.push(newNode);
                existingTargetNodesMap.set(name, newNode); // Track new
             } else {
                 console.log(`Target field "${name}" already exists.`);
             }
        });
        // --- End Node Creation ---

        // --- Update State and Trigger Layout --- 
        setTargets(prevTargets => [...new Set([...prevTargets, ...fieldList])]);
        if (newTargetNodes.length > 0) {
            const finalNodes = [
                ...currentNodes,
                ...newTargetNodes
            ];
            const currentEdges = edges; // No edges added
            const { nodes: layoutedNodes } = getLayoutedElements(finalNodes, currentEdges);
            setNodes(layoutedNodes);
        }
      } catch (error) {
         console.error("Error reading Target Excel file:", error);
         alert(`读取目标 Excel 文件时出错：${error.message}`);
      } finally {
         setIsLoadingTarget(false); 
      }
    };
    reader.onerror = (error) => {
        console.error("FileReader error:", error);
        alert(`文件读取器错误： ${error.message}`);
        setIsLoadingTarget(false); 
    };
    reader.readAsArrayBuffer(file);
  };

  // Function to handle node clicks for click-to-connect and selection styling
  const handleNodeClick = useCallback((event, node) => {
      // --- Click-to-connect logic ---
      if (node.id.startsWith('src-')) {
          // Clicked on a source node
          setSelectedSourceNodeId((prevSelectedId) => 
              prevSelectedId === node.id ? null : node.id // Toggle selection
          );
      } else if (node.id.startsWith('tgt-') && selectedSourceNodeId) {
          // Clicked on a target node while a source node was selected
          const newEdge = {
              id: `edge-${selectedSourceNodeId}-${node.id}`,
              source: selectedSourceNodeId,
              target: node.id,
              animated: true,
          };
          // Check if edge already exists (simple check, might need refinement for complex cases)
          const edgeExists = edges.some(e => e.source === newEdge.source && e.target === newEdge.target);
          if (!edgeExists) {
            setEdges((eds) => addEdge(newEdge, eds));
          }
          setSelectedSourceNodeId(null); // Deselect source node after connecting
      } else {
          // Clicked on a target node without a source selected, or other clicks
          setSelectedSourceNodeId(null); // Deselect any selected source node
      }

      // --- Optional: Update node styles for selection feedback ---
      // This part requires adjusting node data or using className based on selection
      // Example (could be integrated more cleanly):
      setNodes((nds) =>
        nds.map((n) => {
            const isSelected = n.id === selectedSourceNodeId || (n.id.startsWith('src-') && n.id === node.id && selectedSourceNodeId !== node.id);
            // Add/remove a className or style based on selection state
            // This implementation detail depends on how you want to show selection
            // Example using a simple border style change directly (less ideal)
            /*
            if (n.id.startsWith('src-')) {
                 n.style = isSelected ? { ...n.style, border: '2px solid blue' } : { ...n.style, border: '1px solid #bbb' };
            } */
            // A better approach might involve adding a className and styling via CSS
            return n;
        })
      );

  }, [selectedSourceNodeId, setEdges, edges, nodes, setNodes]); // Added nodes/setNodes if modifying styles

  // Function to handle pane clicks (deselect source node)
  const handlePaneClick = useCallback(() => {
    setSelectedSourceNodeId(null);
    // Optional: Reset selection styles if applied
    setNodes((nds) =>
        nds.map((n) => {
            /* Reset styles if needed */
            // if (n.id.startsWith('src-') && n.style?.border.includes('blue')) {
            //     n.style = { ...n.style, border: '1px solid #bbb' };
            // }
            return n;
        })
     );
  }, [setNodes]);

  // Function to handle opening the modal on node double click
  const handleNodeDoubleClick = useCallback((event, node) => {
    if (node.id.startsWith('tgt-')) { // Only allow editing for target nodes
      let initialExpr = '';
      if (node.data.calculationMode === 'manual') {
        initialExpr = node.data.manualExpression;
      } else {
        // Calculate auto expression based on current nodes and edges
        initialExpr = calculateAutoExpressionInternal(node.id, nodes, edges);
      }
      setEditingNodeId(node.id);
      setModalInitialExpression(initialExpr); // Set initial expression for the modal
      setIsModalOpen(true);
    }
  }, [nodes, edges, calculateAutoExpressionInternal]); // Depend on nodes, edges and the helper function

  // Function to handle closing the modal
  const handleCloseModal = useCallback(() => {
    setIsModalOpen(false);
    setEditingNodeId(null);
    setModalInitialExpression(''); // Reset initial expression on close
  }, []);

  // Function to handle saving the expression from the modal
  const handleSaveExpression = useCallback((newExpression) => {
    setNodes((nds) =>
      nds.map((node) => {
        if (node.id === editingNodeId) {
          const isSwitchingToAuto = newExpression === null;
          return {
            ...node,
            data: {
              ...node.data,
              calculationMode: isSwitchingToAuto ? 'auto' : 'manual',
              manualExpression: isSwitchingToAuto ? '' : (newExpression ?? ''), // Ensure it's a string
            },
          };
        }
        return node;
      })
    );
    handleCloseModal();
    // Note: No need to reset modalInitialExpression here, 
    // handleCloseModal does it, and opening sets it again.
  }, [editingNodeId, setNodes, handleCloseModal]);

  // --- Updated Function to handle importing mappings from JSON ---
  const handleImportMappings = (event) => {
    const file = event.target.files[0];
    if (!file) {
      return;
    }
    setIsLoadingMappings(true);
    const reader = new FileReader();

    reader.onload = (e) => {
      let rawMappingsToProcess = null; // Stores the raw array before transformation
      try {
        const parsedData = JSON.parse(e.target.result);

        // --- Detect format and extract raw mappings ---
        // Format A: Root is an array
        if (Array.isArray(parsedData)) {
          rawMappingsToProcess = parsedData;
        } 
        // Format C: Root is an object with field_mappings -> mappings structure
        else if (typeof parsedData === 'object' && parsedData !== null && Array.isArray(parsedData.field_mappings)) {
          let allNestedMappings = [];
          parsedData.field_mappings.forEach((category, catIndex) => {
            // Check if category is an object and has a 'mappings' array
            if (typeof category === 'object' && category !== null && Array.isArray(category.mappings)) {
              // Optionally add category info to the mapping? For now, just concat.
              allNestedMappings = allNestedMappings.concat(category.mappings);
            } else {
                 console.warn(`Skipping category at index ${catIndex} in field_mappings as it doesn't contain a valid 'mappings' array.`);
            }
          });
          rawMappingsToProcess = allNestedMappings;
        }

        // --- Transform and Apply --- 
        if (rawMappingsToProcess !== null) {
          const mappingsToApply = transformRawMappings(rawMappingsToProcess);

          if (mappingsToApply && mappingsToApply.length > 0) {
            console.log(`Importing ${mappingsToApply.length} valid mappings after transformation.`);
            applyMappingsFromJson(mappingsToApply); // Call the main logic function
            // Optional: Success message
            // alert(`成功导入 ${mappingsToApply.length} 条映射规则。`);
          } else if (rawMappingsToProcess.length > 0) {
            // Raw data existed, but transformation removed everything
            throw new Error("JSON 文件内容可解析，但未能提取有效的映射规则 (检查 target_field/target 和 source_field/source_fields 结构)。");
          } else {
            // Raw data structure was valid (e.g., empty array or empty field_mappings) but contained no mappings
            console.log("导入的文件不包含任何可处理的映射规则。");
            alert("导入的文件格式正确，但未找到可应用的映射规则。"); // User feedback
          }
        } else {
          // Neither Format A nor C structure was detected
          throw new Error("无效的 JSON 文件结构。请确保文件是映射数组，或是包含 'field_mappings' 键（其值为包含 'mappings' 数组的对象列表）的对象。");
        }

      } catch (error) {
        console.error("Error parsing or applying JSON mapping:", error);
        // Display specific error messages thrown from checks
        alert(`导入映射失败: ${error.message}`); 
      } finally {
        setIsLoadingMappings(false);
        // Reset file input value
        if (importMappingInputRef.current) {
            importMappingInputRef.current.value = null;
        }
      }
    };

    reader.onerror = (error) => {
      console.error("FileReader error during mapping import:", error);
      alert(`读取映射文件时出错: ${error.message}`);
      setIsLoadingMappings(false);
    };

    reader.readAsText(file);
  };

   // --- Core logic to apply mappings from parsed JSON data (Handles Layout) ---
   const applyMappingsFromJson = (mappings) => {
    // Get current state directly
    const currentNodes = nodes;
    const currentEdges = edges;

    let nodesToAdd = [];
    let edgesToAdd = [];
    let nodeUpdates = {}; // Store updates for existing nodes

    // Use maps for efficient lookups
    const sourceNodesMap = new Map(currentNodes.filter(n => n.id.startsWith('src-')).map(n => [n.data.originalLabel, n]));
    const targetNodesMap = new Map(currentNodes.filter(n => n.id.startsWith('tgt-')).map(n => [n.data.originalLabel, n]));

    // Track existing edges to prevent duplicates
    const existingEdgeSet = new Set(currentEdges.map(e => `${e.source}-${e.target}`));

    mappings.forEach((mapping, index) => {
      const { target: targetLabel, source_fields: sourceLabels, calculation } = mapping;

      if (!targetLabel || !Array.isArray(sourceLabels)) {
        console.warn(`Skipping invalid mapping entry at index ${index}:`, mapping);
        return; // Skip malformed entries
      }

      // --- Find or Create Target Node --- (Remove position calculation)
      let targetNode = targetNodesMap.get(targetLabel);
      if (!targetNode) {
        const nodeId = generateUniqueId('tgt-imported');
        // Remove manual position calculation
        targetNode = {
          id: nodeId,
          data: { originalLabel: targetLabel, calculationMode: 'auto', manualExpression: '' },
          position: { x: 0, y: 0 }, // Dummy position
          type: 'target',
          targetPosition: Position.Left,
        };
        nodesToAdd.push(targetNode);
        targetNodesMap.set(targetLabel, targetNode);
      }

      // --- Find or Create Source Nodes and Edges --- (Remove position calculation)
      let currentMappingSourceNodes = []; 
      sourceLabels.forEach((sourceLabel) => {
         let sourceNode = sourceNodesMap.get(sourceLabel);
         if (!sourceNode) {
           const nodeId = generateUniqueId('src-imported');
           // Remove manual position calculation
           sourceNode = {
             id: nodeId,
             data: { label: sourceLabel, originalLabel: sourceLabel, sourceFile: 'imported' },
             position: { x: 0, y: 0 }, // Dummy position
             type: 'default',
             sourcePosition: Position.Right,
             style: { backgroundColor: '#f0f0f0', width: 'auto', minWidth: '150px' },
           };
           nodesToAdd.push(sourceNode);
           sourceNodesMap.set(sourceLabel, sourceNode);
         }
         currentMappingSourceNodes.push(sourceNode);

         // --- Create Edge --- (Keep as is)
         const edgeId = `edge-${sourceNode.id}-${targetNode.id}`;
         const edgeKey = `${sourceNode.id}-${targetNode.id}`;
         if (!existingEdgeSet.has(edgeKey) && !edgesToAdd.some(e => e.id === edgeId)) {
             edgesToAdd.push({ id: edgeId, source: sourceNode.id, target: targetNode.id, animated: true });
         }
      });

      // --- Determine Calculation Mode and Expression --- (Keep as is)
       const sourceOriginalLabels = currentMappingSourceNodes.map(n => n.data.originalLabel).sort();
       let autoExpr = '';
       if (sourceOriginalLabels.length === 1) {
         autoExpr = sourceOriginalLabels[0];
       } else if (sourceOriginalLabels.length > 1) {
         autoExpr = sourceOriginalLabels.join(' + ');
       }

       let finalCalculationMode = 'auto';
       let finalManualExpression = '';
       if (calculation !== undefined && (calculation !== autoExpr || sourceOriginalLabels.length === 0)) {
         finalCalculationMode = 'manual';
         finalManualExpression = calculation;
       }

       // Store the update for the target node (found or newly created)
       nodeUpdates[targetNode.id] = {
          ...targetNode.data, // Include existing data (like originalLabel, potentially position if updated)
          calculationMode: finalCalculationMode,
          manualExpression: finalManualExpression,
       };

    }); // End mappings loop

    // --- Calculate Final Nodes/Edges --- 
    const updatedNodesPreLayout = currentNodes.map(node => {
       if (nodeUpdates[node.id]) {
           return { ...node, data: { ...node.data, ...nodeUpdates[node.id] } }; 
       }
       return node;
    });
    const finalNodesPreLayout = [...updatedNodesPreLayout, ...nodesToAdd];
    const uniqueNewEdges = edgesToAdd.filter(newEdge => !existingEdgeSet.has(`${newEdge.source}-${newEdge.target}`));
    const finalEdges = [...currentEdges, ...uniqueNewEdges];

    // --- Calculate Layout and Set State --- 
    const { nodes: layoutedNodes } = getLayoutedElements(finalNodesPreLayout, finalEdges);
    setEdges(finalEdges); // Set edges first
    setNodes(layoutedNodes); // Set layouted nodes
   };


  const exportMappings = () => {
    // Use calculateAutoExpressionInternal for consistency
    const currentNodes = nodes; // Get snapshot
    const currentEdges = edges; // Get snapshot
    const targetNodes = currentNodes.filter(n => n.id.startsWith('tgt-'));

    const mappings = targetNodes.map((targetNode) => {
      const targetOriginalLabel = targetNode.data.originalLabel;
      let calculationString = '';

      if (targetNode.data.calculationMode === 'manual') {
        calculationString = targetNode.data.manualExpression;
      } else {
        // Recalculate based on current connections using the internal helper
        calculationString = calculateAutoExpressionInternal(targetNode.id, currentNodes, currentEdges);
      }

       // Find source field labels directly from connections
       const sourceFields = currentEdges
         .filter(e => e.target === targetNode.id)
         .map(e => currentNodes.find(n => n.id === e.source)?.data?.originalLabel)
         .filter(Boolean)
         .sort(); // Sort for consistency in exported JSON

      return {
        target: targetOriginalLabel,
        source_fields: sourceFields, // Use sorted list
        calculation: calculationString,
      };
    });

    if (mappings.length === 0) {
        alert("没有创建任何映射规则，无法导出。");
        return;
    }

    const blob = new Blob([JSON.stringify(mappings, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'flow_field_mapping.json';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  // --- Safely calculate nodeLabel for the modal before returning JSX ---
  let nodeLabelForModal = '';
  // Check if nodes is actually an array and editingNodeId is set
  if (Array.isArray(nodes) && editingNodeId) { 
      const nodeBeingEdited = nodes.find(n => n.id === editingNodeId);
      // Use optional chaining and nullish coalescing for safety
      nodeLabelForModal = nodeBeingEdited?.data?.originalLabel ?? ''; 
  }

  return (
    <ReactFlowProvider>
      {/* Add some basic padding and ensure full height/width potentially */}
      <div className="p-4 h-screen w-screen flex flex-col">
        <h1 className="text-xl font-bold mb-4 text-center">字段映射图形表达式编辑器</h1>

        {/* Control panel section */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4 p-2 border rounded"> {/* Adjusted grid for 3 columns */}
          {/* Source File Upload */}
          <div>
            <label className="block font-semibold mb-1">上传源 Excel 文件 (.xlsx, .xls) (可多选)</label>
            <div className="flex items-center gap-2">
              <input
                className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
                type="file"
                accept=".xlsx,.xls"
                multiple
                onChange={(e) => processSourceFiles(e.target.files)}
                disabled={isLoadingSource || isLoadingMappings} // Disable if importing mappings too
              />
              <label className="whitespace-nowrap">字段行:</label>
              <input
                 type="number"
                 className="border p-1 w-20 rounded"
                 value={sourceRow + 1}
                 min={1}
                 onChange={(e) => setSourceRow(Math.max(0, Number(e.target.value) - 1))}
                 placeholder="行号"
                 disabled={isLoadingSource || isLoadingMappings}
              />
              {isLoadingSource && <span className="text-sm text-gray-500">处理源...</span>}
            </div>
          </div>
          {/* Target File Upload */}
          <div>
            <label className="block font-semibold mb-1">上传目标 Excel 文件 (.xlsx, .xls)</label>
             <div className="flex items-center gap-2">
              <input
                className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => readExcelHeadersTarget(e.target.files[0])} // Use updated target handler
                disabled={isLoadingTarget || isLoadingMappings}
              />
              <label className="whitespace-nowrap">字段行:</label>
              <input type="number" className="border p-1 w-20 rounded" value={targetRow + 1} min={1} onChange={(e) => setTargetRow(Math.max(0, Number(e.target.value) - 1))} placeholder="行号" disabled={isLoadingTarget || isLoadingMappings}/>
               {isLoadingTarget && <span className="text-sm text-gray-500">处理目标...</span>}
            </div>
          </div>
           {/* NEW: Mapping JSON Import */}
           <div>
             <label className="block font-semibold mb-1">导入映射 JSON (.json)</label>
             <div className="flex items-center gap-2">
               <input
                 ref={importMappingInputRef} // Add ref
                 className="block w-full text-sm text-gray-900 border border-gray-300 rounded-lg cursor-pointer bg-gray-50 focus:outline-none"
                 type="file"
                 accept=".json"
                 onChange={handleImportMappings}
                 disabled={isLoadingMappings || isLoadingSource || isLoadingTarget} // Disable during any loading
               />
               {isLoadingMappings && <span className="text-sm text-gray-500">导入中...</span>}
             </div>
           </div>
        </div>

        {/* ReactFlow container - ensure it takes available space */}
        {/* Added flex-grow to make it expand */}
        <div className="flex-grow border border-gray-300 rounded-lg" style={{ minHeight: 400 }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            fitView // Fit view on initial load and node changes might be better
            fitViewOptions={{ padding: 0.1 }} // Add padding to fitView
            onNodeDoubleClick={handleNodeDoubleClick} 
            nodeTypes={nodeTypes} 
            onNodeClick={handleNodeClick} // Add node click handler
            onPaneClick={handlePaneClick} // Add pane click handler
          >
            <MiniMap nodeStrokeWidth={3} zoomable pannable />
            <Controls />
            <Background gap={16} />
          </ReactFlow>
        </div>

        {/* Export button - Centered or placed appropriately */}
        <div className="mt-4 text-center">
            <button
              className="px-6 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors disabled:opacity-50"
              onClick={exportMappings}
              disabled={nodes.length === 0 || isLoadingSource || isLoadingTarget || isLoadingMappings} // Disable if no nodes or loading
            >导出字段映射 JSON</button>
        </div>
      </div>

      {/* Render the modal conditionally */}
      <ExpressionEditorModal 
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSaveExpression}
        initialExpression={modalInitialExpression} 
        nodeLabel={nodeLabelForModal} // Use the safely pre-calculated value
      />
    </ReactFlowProvider>
  );
}
