import { extensionRegistry } from '../registry';
import { HPCPanel } from '../../components/hpc/HPCPanel';

export function registerHPCExtension() {
  extensionRegistry.register({
    id: 'hpc',
    name: 'HPC Portal',
    description: 'High-Performance Computing & Accelerator Orchestration',
    icon: '🏎️',
    component: HPCPanel,
    category: 'tool',
  });
}
