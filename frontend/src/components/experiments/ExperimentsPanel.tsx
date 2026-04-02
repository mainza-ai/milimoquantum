import React, { useState, useEffect } from 'react';
import {
  getExperimentProjects,
  getExperimentRuns,
} from '../../services/api';

interface ExperimentProject {
  id: string;
  name: string;
  created_at: string;
  run_count: number;
}

interface ExperimentRun {
  id: string;
  project_id: string;
  metrics: Record<string, number>;
  params: Record<string, any>;
  status: string;
  created_at: string;
}

export const ExperimentsPanel: React.FC = () => {
  const [projects, setProjects] = useState<ExperimentProject[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingRuns, setLoadingRuns] = useState(false);

  useEffect(() => {
    loadProjects();
  }, []);

  const loadProjects = async () => {
    try {
      const data = await getExperimentProjects();
      setProjects(data.projects || []);
    } catch (error) {
      console.error('Failed to load experiment projects:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadRuns = async (projectId: string) => {
    setLoadingRuns(true);
    try {
      const data = await getExperimentRuns(projectId);
      setRuns(data.runs || []);
      setSelectedProject(projectId);
    } catch (error) {
      console.error('Failed to load runs:', error);
    } finally {
      setLoadingRuns(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400 text-sm">Loading experiments...</div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-2xl">🔬</span>
        <div>
          <h2 className="text-lg font-bold text-white">Experiments</h2>
          <p className="text-xs text-gray-500">Track and compare experiment runs</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {/* Projects List */}
        <div className="col-span-1 bg-white/[0.02] border border-white/[0.06] rounded-lg p-4">
          <h3 className="text-sm font-medium text-white mb-3">Projects</h3>
          {projects.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-4">No projects yet</p>
          ) : (
            <div className="space-y-2">
              {projects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => loadRuns(project.id)}
                  className={`w-full text-left p-3 rounded transition-colors ${
                    selectedProject === project.id
                      ? 'bg-cyan-500/10 border border-cyan-500/20'
                      : 'bg-black/20 hover:bg-white/[0.04]'
                  }`}
                >
                  <div className="text-sm text-white">{project.name}</div>
                  <div className="text-xs text-gray-500">
                    {project.run_count || 0} runs
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Runs List */}
        <div className="col-span-2 bg-white/[0.02] border border-white/[0.06] rounded-lg p-4">
          <h3 className="text-sm font-medium text-white mb-3">Runs</h3>
          {!selectedProject ? (
            <p className="text-sm text-gray-500 text-center py-8">
              Select a project to view runs
            </p>
          ) : loadingRuns ? (
            <div className="text-center py-8 text-gray-400 text-sm">Loading runs...</div>
          ) : runs.length === 0 ? (
            <p className="text-sm text-gray-500 text-center py-8">No runs in this project</p>
          ) : (
            <div className="space-y-4">
              {runs.map((run) => (
                <div
                  key={run.id}
                  className="p-4 bg-black/20 rounded border border-white/[0.04]"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-xs text-gray-400 font-mono">
                      {run.id.slice(0, 8)}
                    </span>
                    <span
                      className={`text-xs px-2 py-0.5 rounded ${
                        run.status === 'completed'
                          ? 'bg-green-500/10 text-green-400'
                          : run.status === 'running'
                          ? 'bg-blue-500/10 text-blue-400'
                          : 'bg-red-500/10 text-red-400'
                      }`}
                    >
                      {run.status}
                    </span>
                  </div>

                  {/* Metrics */}
                  {run.metrics && Object.keys(run.metrics).length > 0 && (
                    <div className="mb-2">
                      <div className="text-[10px] text-gray-500 uppercase mb-1">Metrics</div>
                      <div className="grid grid-cols-3 gap-2">
                        {Object.entries(run.metrics).map(([key, value]) => (
                          <div key={key} className="text-xs">
                            <span className="text-gray-400">{key}:</span>{' '}
                            <span className="text-white font-mono">
                              {typeof value === 'number' ? value.toFixed(4) : value}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Params */}
                  {run.params && Object.keys(run.params).length > 0 && (
                    <div>
                      <div className="text-[10px] text-gray-500 uppercase mb-1">Parameters</div>
                      <div className="text-xs text-gray-400">
                        {Object.entries(run.params)
                          .map(([k, v]) => `${k}=${v}`)
                          .join(', ')}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
