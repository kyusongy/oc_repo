interface Props {
  command: string;
  description: string;
  resolved?: boolean;
  onApprove: () => void;
  onDeny: () => void;
}

export function ApprovalCard({ command, description, resolved, onApprove, onDeny }: Props) {
  return (
    <div className="mb-3 mx-2 border border-amber-200 bg-amber-50 rounded-lg p-4">
      <p className="text-sm text-gray-700 mb-2">{description}</p>
      <pre className="text-xs font-mono bg-gray-900 text-green-400 p-3 rounded-md mb-3 overflow-x-auto">
        {command}
      </pre>
      {resolved ? (
        <p className="text-xs text-gray-500 italic">Responded</p>
      ) : (
        <div className="flex gap-2">
          <button onClick={onApprove} className="px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700 transition-colors">
            Approve
          </button>
          <button onClick={onDeny} className="px-4 py-2 bg-red-100 text-red-700 text-sm font-medium rounded-md hover:bg-red-200 transition-colors">
            Deny
          </button>
        </div>
      )}
    </div>
  );
}
