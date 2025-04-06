import React, { useState, useEffect } from 'react';

export default function ExpressionEditorModal({ 
    isOpen, 
    onClose, 
    onSave, 
    initialExpression = '', 
    nodeLabel = '' 
}) {
  const [expression, setExpression] = useState(initialExpression);

  // Update local state if the initial expression changes (e.g., opening modal for a different node)
  useEffect(() => {
    setExpression(initialExpression);
  }, [initialExpression, isOpen]); // Depend on isOpen to reset when modal reopens

  if (!isOpen) {
    return null;
  }

  const handleSave = () => {
    onSave(expression); // Pass the current expression state
  };

  const handleSwitchToAuto = () => {
    onSave(null); // Pass null to indicate switching to auto mode
  };

  return (
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50"
      onClick={onClose} // Close if clicking outside the modal content
    >
      <div 
        className="bg-white p-6 rounded-lg shadow-xl w-full max-w-md relative"
        onClick={(e) => e.stopPropagation()} // Prevent closing when clicking inside
      >
        <h2 className="text-lg font-semibold mb-4">编辑表达式: {nodeLabel}</h2>
        
        <textarea
          className="w-full p-2 border border-gray-300 rounded mb-4 h-24 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
          value={expression}
          onChange={(e) => setExpression(e.target.value)}
          placeholder="例如: 源字段A * 0.5 + 源字段B"
        />
        
        <div className="flex justify-between items-center">
          <button 
            onClick={handleSwitchToAuto}
            className="text-sm text-blue-600 hover:underline"
          >
            切换回自动模式 (根据连线)
          </button>
          <div className="flex gap-2">
            <button 
              onClick={onClose}
              className="px-4 py-2 bg-gray-300 text-gray-800 rounded hover:bg-gray-400 transition-colors"
            >
              取消
            </button>
            <button 
              onClick={handleSave}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              保存手动表达式
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 