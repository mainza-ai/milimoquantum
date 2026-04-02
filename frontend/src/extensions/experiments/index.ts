import { extensionRegistry } from '../registry';
import { ExperimentsPanel } from '../../components/experiments/ExperimentsPanel';

export function registerExperimentsExtension() {
  extensionRegistry.register({
    id: 'experiments',
    name: 'Experiments',
    description: 'Track and compare experiment runs',
    icon: '🔬',
    component: ExperimentsPanel,
    category: 'tool',
  });
}
