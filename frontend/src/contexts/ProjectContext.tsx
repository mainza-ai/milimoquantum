import { createContext, useContext, useState, useEffect } from 'react';
import { fetchWithAuth } from '../services/api';
import type { ReactNode } from 'react';

interface Project {
    id: string;
    name: string;
    description: string;
}

interface ProjectContextType {
    activeProjectId: string | null;
    activeProject: Project | null;
    setActiveProjectId: (id: string | null) => void;
    clearActiveProject: () => void;
}

const ProjectContext = createContext<ProjectContextType | undefined>(undefined);

export function ProjectProvider({ children }: { children: ReactNode }) {
    const [activeProjectId, setActiveProjectIdState] = useState<string | null>(() => {
        return localStorage.getItem('mq_active_project_id');
    });
    const [activeProject, setActiveProject] = useState<Project | null>(null);

    useEffect(() => {
        if (activeProjectId) {
            localStorage.setItem('mq_active_project_id', activeProjectId);
            // Fetch project details if needed
            fetchWithAuth(`/api/projects/${activeProjectId}`)
                .then(res => res.json())
                .then(data => {
                    if (data.project) {
                        setActiveProject(data.project);
                    }
                })
                .catch(() => {
                    // If project doesn't exist anymore or error, clear
                    console.error("Failed to fetch active project details");
                });
        } else {
            localStorage.removeItem('mq_active_project_id');
            setActiveProject(null);
        }
    }, [activeProjectId]);

    const setActiveProjectId = (id: string | null) => {
        setActiveProjectIdState(id);
    };

    const clearActiveProject = () => {
        setActiveProjectIdState(null);
    };

    return (
        <ProjectContext.Provider value={{
            activeProjectId,
            activeProject,
            setActiveProjectId,
            clearActiveProject
        }}>
            {children}
        </ProjectContext.Provider>
    );
}

export function useProject() {
    const context = useContext(ProjectContext);
    if (context === undefined) {
        throw new Error('useProject must be used within a ProjectProvider');
    }
    return context;
}
