import { extensionRegistry } from '../registry';
import { AuditDashboard } from '../../components/admin/AuditDashboard';

export function registerAuditExtension() {
    extensionRegistry.register({
        id: 'audit',
        name: 'Audit Dashboard',
        description: 'Security & Compliance Monitoring',
        icon: '🛡️',
        component: AuditDashboard,
        category: 'tool',
    });
}
