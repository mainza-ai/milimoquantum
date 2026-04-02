import React, { useState, useEffect } from 'react';
import {
  getHPCStatus,
  submitHPCJob,
  getHPCJobStatus,
} from '../../services/api';

interface HPCJob {
  id: string;
  name: string;
  status: string;
  cores: number;
  memory: string;
  created_at: string;
  completed_at?: string;
  result?: string;
}

export const HPCPanel: React.FC = () => {
  const [status, setStatus] = useState<any>(null);
  const [jobs, setJobs] = useState<HPCJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [newJob, setNewJob] = useState({
    name: '',
    script: '',
    cores: 4,
    memory: '8GB',
  });

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const data = await getHPCStatus();
      setStatus(data);
      if (data.jobs) {
        setJobs(data.jobs);
      }
    } catch (error) {
      console.error('Failed to load HPC status:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newJob.name || !newJob.script) return;

    setSubmitting(true);
    try {
      const result = await submitHPCJob(newJob);
      if (result.job_id) {
        setJobs([
          {
            id: result.job_id,
            name: newJob.name,
            status: 'pending',
            cores: newJob.cores,
            memory: newJob.memory,
            created_at: new Date().toISOString(),
          },
          ...jobs,
        ]);
        setNewJob({ name: '', script: '', cores: 4, memory: '8GB' });
      }
    } catch (error) {
      console.error('Failed to submit job:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const refreshJobStatus = async (jobId: string) => {
    try {
      const data = await getHPCJobStatus(jobId);
      setJobs(jobs.map((j) => (j.id === jobId ? { ...j, ...data } : j)));
    } catch (error) {
      console.error('Failed to refresh job status:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-gray-400 text-sm">Loading HPC status...</div>
      </div>
    );
  }

  return (
    <div className="h-full overflow-auto p-6">
      <div className="flex items-center gap-3 mb-6">
        <span className="text-2xl">🏎️</span>
        <div>
          <h2 className="text-lg font-bold text-white">HPC Portal</h2>
          <p className="text-xs text-gray-500">High-Performance Computing Job Manager</p>
        </div>
      </div>

      {/* Status Card */}
      {status && (
        <div className="bg-white/[0.02] border border-white/[0.06] rounded-lg p-4 mb-6">
          <h3 className="text-sm font-medium text-white mb-3">System Status</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-[10px] text-gray-500 uppercase mb-1">MPI Available</div>
              <div className={`text-sm ${status.mpi_available ? 'text-green-400' : 'text-red-400'}`}>
                {status.mpi_available ? '✓ Yes' : '✗ No'}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-500 uppercase mb-1">GPU Available</div>
              <div className={`text-sm ${status.gpu_available ? 'text-green-400' : 'text-gray-400'}`}>
                {status.gpu_available ? '✓ Yes' : '✗ No'}
              </div>
            </div>
            <div>
              <div className="text-[10px] text-gray-500 uppercase mb-1">CPU Cores</div>
              <div className="text-sm text-white">{status.cpu_cores || 'N/A'}</div>
            </div>
            <div>
              <div className="text-[10px] text-gray-500 uppercase mb-1">Total Memory</div>
              <div className="text-sm text-white">{status.total_memory || 'N/A'}</div>
            </div>
          </div>
        </div>
      )}

      {/* Submit Job Form */}
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-lg p-4 mb-6">
        <h3 className="text-sm font-medium text-white mb-3">Submit New Job</h3>
        <form onSubmit={handleSubmitJob} className="space-y-4">
          <div>
            <label className="block text-[10px] text-gray-500 uppercase mb-1">Job Name</label>
            <input
              type="text"
              value={newJob.name}
              onChange={(e) => setNewJob({ ...newJob, name: e.target.value })}
              className="w-full px-3 py-2 bg-black/20 border border-white/[0.06] rounded text-sm text-white"
              placeholder="my-quantum-job"
            />
          </div>
          <div>
            <label className="block text-[10px] text-gray-500 uppercase mb-1">Script</label>
            <textarea
              value={newJob.script}
              onChange={(e) => setNewJob({ ...newJob, script: e.target.value })}
              className="w-full px-3 py-2 bg-black/20 border border-white/[0.06] rounded text-sm text-white font-mono"
              rows={4}
              placeholder="#!/bin/bash&#10;python quantum_script.py"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-[10px] text-gray-500 uppercase mb-1">Cores</label>
              <input
                type="number"
                value={newJob.cores}
                onChange={(e) => setNewJob({ ...newJob, cores: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 bg-black/20 border border-white/[0.06] rounded text-sm text-white"
                min={1}
                max={64}
              />
            </div>
            <div>
              <label className="block text-[10px] text-gray-500 uppercase mb-1">Memory</label>
              <select
                value={newJob.memory}
                onChange={(e) => setNewJob({ ...newJob, memory: e.target.value })}
                className="w-full px-3 py-2 bg-black/20 border border-white/[0.06] rounded text-sm text-white"
              >
                <option value="4GB">4 GB</option>
                <option value="8GB">8 GB</option>
                <option value="16GB">16 GB</option>
                <option value="32GB">32 GB</option>
                <option value="64GB">64 GB</option>
              </select>
            </div>
          </div>
          <button
            type="submit"
            disabled={submitting || !newJob.name || !newJob.script}
            className="w-full py-2 bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 rounded text-sm font-medium hover:bg-cyan-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Submitting...' : 'Submit Job'}
          </button>
        </form>
      </div>

      {/* Jobs List */}
      <div className="bg-white/[0.02] border border-white/[0.06] rounded-lg p-4">
        <h3 className="text-sm font-medium text-white mb-3">Active Jobs</h3>
        {jobs.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-4">No jobs submitted</p>
        ) : (
          <div className="space-y-2">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="flex items-center justify-between p-3 bg-black/20 rounded"
              >
                <div className="flex-1">
                  <div className="text-sm text-white">{job.name}</div>
                  <div className="text-xs text-gray-500">
                    {job.cores} cores • {job.memory}
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span
                    className={`px-2 py-0.5 rounded text-xs ${
                      job.status === 'completed'
                        ? 'bg-green-500/10 text-green-400'
                        : job.status === 'running'
                        ? 'bg-blue-500/10 text-blue-400'
                        : job.status === 'failed'
                        ? 'bg-red-500/10 text-red-400'
                        : 'bg-yellow-500/10 text-yellow-400'
                    }`}
                  >
                    {job.status}
                  </span>
                  <button
                    onClick={() => refreshJobStatus(job.id)}
                    className="text-gray-400 hover:text-white transition-colors"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                      />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
