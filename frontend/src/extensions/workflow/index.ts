import { extensionRegistry } from '../registry';
import { WorkflowBuilder } from '../../components/workflow/WorkflowBuilder';

export function registerWorkflowExtension() {
    extensionRegistry.register({
        id: 'workflow',
        name: 'Workflow Builder',
        description: 'Multi-step Quantum Workflow Orchestration',
        icon: '⚡',
        component: WorkflowBuilder,
        category: 'tool',
    });
}
