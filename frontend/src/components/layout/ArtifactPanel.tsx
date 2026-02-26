/* Milimo Quantum — Artifact Panel (Enhanced)
 *
 * Features:
 * - Monaco editor for code with edit/re-run
 * - Copy-to-clipboard with feedback
 * - Download code as .py file
 * - Interactive results histogram
 * - Circuit text rendering
 */
import { CodeView } from '../artifacts/CodeView';
import { CircuitView } from '../artifacts/CircuitView';
import { ResultsView } from '../artifacts/ResultsView';
import { NotebookView } from '../artifacts/NotebookView';
import { ReportView } from '../artifacts/ReportView';
import { DatasetView } from '../artifacts/DatasetView';
import type { Artifact } from '../../types';

interface ArtifactPanelProps {
    artifact: Artifact | null;
    onClose: () => void;
}

export function ArtifactPanel({ artifact, onClose }: ArtifactPanelProps) {
    if (!artifact) return null;

    return (
        <div className="w-[420px] shrink-0 border-l border-mq-border bg-mq-void
      flex flex-col animate-slide-in-right overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between px-5 py-4 border-b border-mq-border">
                <div className="flex items-center gap-2.5 min-w-0">
                    <ArtifactTypeIcon type={artifact.type} />
                    <h3 className="text-[13px] font-semibold text-mq-text truncate tracking-tight">
                        {artifact.title}
                    </h3>
                </div>
                <button
                    onClick={onClose}
                    className="w-7 h-7 rounded-lg flex items-center justify-center
            text-mq-text-tertiary hover:text-mq-text text-xs
            hover:bg-mq-hover transition-all duration-200 cursor-pointer"
                >
                    ✕
                </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-auto p-5">
                {artifact.type === 'code' && <CodeView content={artifact.content} language={artifact.language} title={artifact.title} />}
                {artifact.type === 'circuit' && <CircuitView content={artifact.content} metadata={artifact.metadata} />}
                {artifact.type === 'results' && <ResultsView content={artifact.content} metadata={artifact.metadata} />}
                {artifact.type === 'notebook' && <NotebookView content={artifact.content} metadata={artifact.metadata} />}
                {artifact.type === 'report' && <ReportView content={artifact.content} metadata={artifact.metadata} />}
                {artifact.type === 'dataset' && <DatasetView content={artifact.content} metadata={artifact.metadata} />}
            </div>
        </div>
    );
}

function ArtifactTypeIcon({ type }: { type: string }) {
    const icons: Record<string, string> = { code: '💻', circuit: '🔌', results: '📊', notebook: '📓', report: '📄', dataset: '🗄️' };
    return <span className="text-[15px] shrink-0">{icons[type] || '📄'}</span>;
}

