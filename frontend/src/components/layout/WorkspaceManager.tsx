import { useWorkspace } from '../../contexts/WorkspaceContext';
import { extensionRegistry } from '../../extensions/registry';

interface WorkspaceManagerProps {
    currentConversationId?: string;
    loadConversation: (id: string) => void;
}

export function WorkspaceManager({ currentConversationId, loadConversation }: WorkspaceManagerProps) {
    const { activeExtensions, closeExtension } = useWorkspace();

    return (
        <>
            {activeExtensions.map((active: any) => {
                const ext = extensionRegistry.get(active.extensionId);
                if (!ext) return null;
                const Component = ext.component as any;
                return (
                    <Component
                        key={active.id}
                        instanceId={active.id}
                        isOpen={active.isOpen}
                        onClose={() => closeExtension(active.id)}
                        currentConversationId={currentConversationId}
                        onLoadConversation={loadConversation}
                        {...active.props}
                    />
                );
            })}
        </>
    );
}
