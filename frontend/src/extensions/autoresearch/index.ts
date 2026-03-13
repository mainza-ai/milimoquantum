import { extensionRegistry } from '../registry';
import { AutoresearchPanel } from './AutoresearchPanel';

export function registerAutoresearchExtension() {
    extensionRegistry.register({
        id: 'autoresearch',
        name: 'Autoresearch-MLX',
        description: 'Autonomous hardware training loops',
        icon: '🚀',
        component: AutoresearchPanel,
        category: 'science',
        isWindow: true
    });
}
