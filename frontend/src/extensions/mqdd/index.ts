import { extensionRegistry } from '../registry';
import { DrugDiscoveryPanel } from './DrugDiscoveryPanel';

export function registerMQDDExtension() {
    extensionRegistry.register({
        id: 'mqdd',
        name: 'Drug Discovery',
        description: 'Quantum Molecular Simulations',
        icon: '🧬',
        component: DrugDiscoveryPanel,
        category: 'science',
        isWindow: true
    });
}
