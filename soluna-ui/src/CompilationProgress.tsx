import React from 'react';
import { IconClose } from './Icons';

type CompilationProgressProps = {
  stage: 'idle' | 'lexing' | 'parsing' | 'semantic' | 'codegen' | 'complete' | 'error';
  percentage: number;
  message: string;
  timestamp: number;
  onStop?: () => void;
};

const stageLabels: Record<string, string> = {
  idle: 'Idle',
  lexing: 'Lexing',
  parsing: 'Parsing',
  semantic: 'Semantic Analysis',
  codegen: 'Code Generation',
  complete: 'Complete',
  error: 'Error',
};

const stages = ['lexing', 'parsing', 'semantic', 'codegen'];

export const CompilationProgress: React.FC<CompilationProgressProps> = ({ 
  stage, 
  percentage, 
  message,
  onStop
}) => {
  // Only show when actively compiling (not idle or complete)
  const isVisible = stage !== 'idle' && stage !== 'complete';

  if (!isVisible) return null;

  const currentStageIndex = stages.findIndex(s => s === stage);

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 pointer-events-none">
      <div className="bg-zinc-950 border border-zinc-700 rounded-lg shadow-2xl w-96 pointer-events-auto overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-zinc-700 flex items-center justify-between bg-zinc-900/50">
          <div>
            <h3 className="text-zinc-100 font-semibold text-sm uppercase tracking-wide">
              Compiling: {stageLabels[stage]}
            </h3>
            <p className="text-zinc-500 text-xs mt-1">{message}</p>
          </div>
          <button
            onClick={onStop}
            className="text-zinc-600 hover:text-zinc-300 transition-colors p-1 rounded hover:bg-zinc-800"
            title="Stop compilation"
          >
            <IconClose />
          </button>
        </div>

        {/* Progress Section */}
        <div className="px-6 py-5">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-zinc-400 uppercase tracking-wide">
              Progress
            </span>
            <span className="text-sm font-semibold text-zinc-200">{percentage}%</span>
          </div>

          <div className="w-full bg-zinc-800 rounded h-2 overflow-hidden">
            <div
              className="h-full bg-zinc-400 transition-all duration-300"
              style={{ width: `${percentage}%` }}
            />
          </div>

          {/* Stage indicators */}
          <div className="mt-6 space-y-2">
            {stages.map((s, idx) => {
              const isCompleted = idx < currentStageIndex;
              const isCurrent = idx === currentStageIndex;

              return (
                <div
                  key={s}
                  className="flex items-center gap-3"
                >
                  <div
                    className={`flex-shrink-0 w-5 h-5 rounded border transition-all ${
                      isCurrent
                        ? 'border-zinc-300 bg-zinc-400'
                        : isCompleted
                        ? 'border-zinc-500 bg-zinc-700'
                        : 'border-zinc-700 bg-transparent'
                    }`}
                  >
                    {(isCurrent || isCompleted) && (
                      <div className={`w-full h-full flex items-center justify-center text-[10px] font-bold ${isCurrent ? 'text-black' : 'text-zinc-300'}`}>
                        {isCompleted ? '✓' : '•'}
                      </div>
                    )}
                  </div>
                  <span
                    className={`text-xs font-medium uppercase tracking-wide ${
                      isCurrent
                        ? 'text-zinc-100'
                        : isCompleted
                        ? 'text-zinc-500'
                        : 'text-zinc-700'
                    }`}
                  >
                    {stageLabels[s]}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Footer */}
        <div className="bg-zinc-900/30 px-6 py-3 border-t border-zinc-700 flex justify-end gap-3">
          <button
            onClick={onStop}
            className="px-3 py-1.5 bg-zinc-800 border border-zinc-700 text-zinc-300 rounded text-xs font-medium uppercase tracking-wide hover:bg-zinc-700 transition-colors"
          >
            Stop
          </button>
        </div>
      </div>
    </div>
  );
};