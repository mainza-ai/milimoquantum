import { extensionRegistry } from '../registry';
import { GraphPanel } from '../../components/graph/GraphPanel';

export function registerGraphExtension() {
    extensionRegistry.register({
        id: 'graph',
        name: 'Graph Intelligence',
        description: 'Knowledge Graph & Agent Memory',
        icon: '🕸️',
        component: GraphPanel,
        category: 'tool',
    });
}
