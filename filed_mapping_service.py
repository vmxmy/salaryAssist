import React, { useState } from 'react';

export default function FieldMapping() {
  const [sources, setSources] = useState([
    '基本工资',
    '岗位工资',
    '绩效A',
    '绩效B',
    '工龄工资',
  ]);
  const [targets, setTargets] = useState([
    '应发工资',
    '绩效合计',
    '实发工资'
  ]);
  const [mappings, setMappings] = useState([]);
  const [selectedSource, setSelectedSource] = useState('');
  const [selectedTarget, setSelectedTarget] = useState('');

  const addMapping = () => {
    if (selectedSource && selectedTarget) {
      setMappings([...mappings, { source: selectedSource, target: selectedTarget }]);
      setSelectedSource('');
      setSelectedTarget('');
    }
  };

  return (
    <div className="p-4">
      <h1 className="text-xl font-bold mb-4">字段映射配置</h1>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <h2 className="font-semibold mb-2">源字段</h2>
          <select
            className="w-full border rounded p-2"
            value={selectedSource}
            onChange={(e) => setSelectedSource(e.target.value)}
          >
            <option value="">请选择源字段</option>
            {sources.map((src) => (
              <option key={src} value={src}>{src}</option>
            ))}
          </select>
        </div>

        <div>
          <h2 className="font-semibold mb-2">目标字段</h2>
          <select
            className="w-full border rounded p-2"
            value={selectedTarget}
            onChange={(e) => setSelectedTarget(e.target.value)}
          >
            <option value="">请选择目标字段</option>
            {targets.map((tgt) => (
              <option key={tgt} value={tgt}>{tgt}</option>
            ))}
          </select>
        </div>
      </div>

      <button
        className="mt-4 px-4 py-2 bg-blue-500 text-white rounded"
        onClick={addMapping}
      >
        {"➕ 添加映射"}
      </button>


      <div className="mt-6">
        <h2 className="font-semibold mb-2">当前映射关系</h2>
        {mappings.length === 0 && <p className="text-gray-500">暂无映射</p>}
        <ul className="list-disc pl-5">
          {mappings.map((map, i) => (
             <li key={i}>{map.source} -> {map.target}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
