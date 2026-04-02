import { extensionRegistry } from '../registry';
import { HPCPortal } from '../../components/hpc/HPCPortal';

export function registerHPCExtension() {
    extensionRegistry.register({
        id: 'hpc',
        name: 'HPC Portal',
        description: 'High-Performance Computing & Accelerator Orchestration',
        icon: '🏎️',
        component: HPCPortal,
        category: 'tool',
    });
}
