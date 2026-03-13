import React from 'react';

/**
 * Milimo OS Extension Definition
 */
export interface Extension {
    id: string;
    name: string;
    description: string;
    icon: string; // Emoji or SVG string
    component: React.LazyExoticComponent<React.FC<any>> | React.FC<any>;
    category: 'core' | 'science' | 'industry' | 'advanced' | 'tool';
    isWindow?: boolean; // If true, opens in a movable window instead of full replace
    defaultWidth?: number;
    defaultHeight?: number;
}

class ExtensionRegistry {
    private extensions: Map<string, Extension> = new Map();

    register(ext: Extension) {
        this.extensions.set(ext.id, ext);
        console.log(`[Milimo OS] Registered extension: ${ext.name} (${ext.id})`);
    }

    get(id: string): Extension | undefined {
        return this.extensions.get(id);
    }

    getAll(): Extension[] {
        return Array.from(this.extensions.values());
    }

    getByCategory(category: Extension['category']): Extension[] {
        return this.getAll().filter(ext => ext.category === category);
    }
}

export const extensionRegistry = new ExtensionRegistry();
