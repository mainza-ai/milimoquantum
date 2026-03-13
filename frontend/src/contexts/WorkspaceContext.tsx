import { createContext, useContext, useState, type ReactNode } from 'react';
import { extensionRegistry } from '../extensions/registry';

export interface ActiveExtension {
    id: string; // Unique instance ID
    extensionId: string;
    isOpen: boolean;
    isMinimized: boolean;
    isMaximized: boolean;
    zIndex: number;
    props?: Record<string, any>;
}

interface WorkspaceContextType {
    activeExtensions: ActiveExtension[];
    openExtension: (extensionId: string, props?: Record<string, any>) => void;
    closeExtension: (instanceId: string) => void;
    minimizeExtension: (instanceId: string) => void;
    maximizeExtension: (instanceId: string) => void;
    bringToFront: (instanceId: string) => void;
    closeAll: () => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

export function WorkspaceProvider({ children }: { children: ReactNode }) {
    const [activeExtensions, setActiveExtensions] = useState<ActiveExtension[]>([]);

    const openExtension = (extensionId: string, props?: Record<string, any>) => {
        const ext = extensionRegistry.get(extensionId);
        if (!ext) {
            console.error(`[Milimo OS] Extension not found: ${extensionId}`);
            return;
        }

        // If it's not a windowed extension, close others that aren't windows
        // For now, we'll keep it simple: just add it to the active list
        const isSingleton = true; // Many apps might want to be singletons

        setActiveExtensions(prev => {
            if (isSingleton) {
                const existing = prev.find(e => e.extensionId === extensionId);
                if (existing) {
                    return prev.map(e => e.id === existing.id ? { ...e, isOpen: true, isMinimized: false, zIndex: Math.max(...prev.map(p => p.zIndex), 0) + 1 } : e);
                }
            }
            
            return [...prev, {
                id: `${extensionId}-${Date.now()}`,
                extensionId,
                isOpen: true,
                isMinimized: false,
                isMaximized: false,
                zIndex: Math.max(...prev.map(p => p.zIndex), 0) + 1,
                props
            }];
        });
    };

    const closeExtension = (instanceId: string) => {
        setActiveExtensions(prev => prev.filter(e => e.id !== instanceId));
    };

    const minimizeExtension = (instanceId: string) => {
        setActiveExtensions(prev => prev.map(e => e.id === instanceId ? { ...e, isMinimized: true } : e));
    };

    const maximizeExtension = (instanceId: string) => {
        setActiveExtensions(prev => prev.map(e => e.id === instanceId ? { ...e, isMaximized: !e.isMaximized } : e));
    };

    const bringToFront = (instanceId: string) => {
        setActiveExtensions(prev => {
            const maxZ = Math.max(...prev.map(p => p.zIndex), 0);
            return prev.map(e => e.id === instanceId ? { ...e, zIndex: maxZ + 1 } : e);
        });
    };

    const closeAll = () => {
        setActiveExtensions([]);
    };

    return (
        <WorkspaceContext.Provider value={{
            activeExtensions,
            openExtension,
            closeExtension,
            minimizeExtension,
            maximizeExtension,
            bringToFront,
            closeAll
        }}>
            {children}
        </WorkspaceContext.Provider>
    );
}

export function useWorkspace() {
    const context = useContext(WorkspaceContext);
    if (context === undefined) {
        throw new Error('useWorkspace must be used within a WorkspaceProvider');
    }
    return context;
}
