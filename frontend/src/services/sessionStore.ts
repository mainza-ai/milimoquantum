/**
 * Milimo OS — Extension Session Store
 * 
 * Simple singleton to persist data for extensions based on their unique instance IDs.
 * This prevents data loss when a panel is closed but the conversation is still active.
 */

class ExtensionSessionStore {
    private PREFIX = 'mq_ext_';

    /**
     * Set data for a specific instance
     */
    set(instanceId: string, data: any) {
        try {
            localStorage.setItem(this.PREFIX + instanceId, JSON.stringify(data));
        } catch (e) {
            console.error("Failed to save session data", e);
        }
    }

    /**
     * Get data for a specific instance
     */
    get<T>(instanceId: string): T | null {
        const raw = localStorage.getItem(this.PREFIX + instanceId);
        if (!raw) return null;
        try {
            return JSON.parse(raw) as T;
        } catch (e) {
            console.error("Failed to parse session data", e);
            return null;
        }
    }

    /**
     * Remove data for a specific instance
     */
    remove(instanceId: string) {
        localStorage.removeItem(this.PREFIX + instanceId);
    }

    /**
     * Clear all session data (e.g., on logout or new chat)
     */
    clearAll() {
        Object.keys(localStorage)
            .filter(key => key.startsWith(this.PREFIX))
            .forEach(key => localStorage.removeItem(key));
    }
}

export const extensionSessionStore = new ExtensionSessionStore();
