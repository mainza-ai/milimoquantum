import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, FlatList, TouchableOpacity, ActivityIndicator, SafeAreaView, StatusBar, RefreshControl } from 'react-native';

const API_URL = 'http://localhost:8000/api';

export default function App() {
    const [runs, setRuns] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [error, setError] = useState(null);

    const fetchRuns = async () => {
        try {
            const response = await fetch(`${API_URL}/experiments/runs/default`);
            if (!response.ok) throw new Error('Network response was not ok');
            const data = await response.json();
            setRuns(data.runs || []);
            setError(null);
        } catch (err) {
            console.log('Fetch error:', err);
            // Fallback data for showcase
            setError('Unable to fetch from API. Showing cached jobs.');
            setRuns([
                { run_id: 'job-1234', circuit_name: 'Bell State Prep', status: 'COMPLETED', backend: 'aer_simulator' },
                { run_id: 'job-5678', circuit_name: 'VQE H2 Molecule', status: 'RUNNING', backend: 'ibm_kyiv' },
                { run_id: 'job-9012', circuit_name: 'Shor Algorithm', status: 'QUEUED', backend: 'amazon_braket_sv1' }
            ]);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    useEffect(() => {
        fetchRuns();
    }, []);

    const onRefresh = () => {
        setRefreshing(true);
        fetchRuns();
    };

    const dispatchJob = async () => {
        setLoading(true);
        try {
            const response = await fetch(`${API_URL}/jobs/execute-code`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: "import time\nimport math\n\n# Simulate a heavy benchmark\ntime.sleep(5)\nprint(f'Benchmark completed. Pi approx: {math.pi}')\n"
                })
            });
            if (!response.ok) throw new Error('Failed to dispatch job');
            const data = await response.json();

            // Add the new queued job to the top of the list locally
            const newJob = {
                run_id: data.job_id,
                circuit_name: 'Sandbox Benchmark',
                status: data.status || 'QUEUED',
                backend: 'celery_worker'
            };
            setRuns(prev => [newJob, ...prev]);
        } catch (err) {
            console.log('Dispatch error:', err);
            setError('Unable to dispatch job. API might be offline.');
        } finally {
            setLoading(false);
        }
    };

    const getStatusColor = (status) => {
        switch (status) {
            case 'COMPLETED': return '#10b981';
            case 'SUCCESS': return '#10b981';
            case 'RUNNING': return '#3b82f6';
            case 'QUEUED': return '#f59e0b';
            case 'PENDING': return '#f59e0b';
            case 'FAILED': return '#ef4444';
            default: return '#6b7280';
        }
    };

    const renderItem = ({ item }) => (
        <View style={styles.card}>
            <View style={styles.cardHeader}>
                <Text style={styles.circuitName}>{item.circuit_name || item.name || 'Anonymous Job'}</Text>
                <View style={[styles.badge, { backgroundColor: getStatusColor(item.status) + '20' }]}>
                    <Text style={[styles.badgeText, { color: getStatusColor(item.status) }]}>
                        {item.status || 'UNKNOWN'}
                    </Text>
                </View>
            </View>
            <View style={styles.cardBody}>
                <Text style={styles.detailText}>ID: {item.run_id || item.id}</Text>
                <Text style={styles.detailText}>Backend: {item.backend}</Text>
            </View>
        </View>
    );

    return (
        <SafeAreaView style={styles.container}>
            <StatusBar barStyle="light-content" />
            <View style={styles.header}>
                <View>
                    <Text style={styles.headerTitle}>Milimo Quantum</Text>
                    <Text style={styles.headerSubtitle}>Enterprise Job Monitor</Text>
                </View>
                <TouchableOpacity style={styles.runButton} onPress={dispatchJob} disabled={loading}>
                    <Text style={styles.runButtonText}>+ New Job</Text>
                </TouchableOpacity>
            </View>

            {error && (
                <View style={styles.errorContainer}>
                    <Text style={styles.errorText}>{error}</Text>
                </View>
            )}

            {loading && !refreshing ? (
                <View style={styles.loaderContainer}>
                    <ActivityIndicator size="large" color="#3b82f6" />
                    <Text style={styles.loaderText}>Connecting to Cluster...</Text>
                </View>
            ) : (
                <FlatList
                    data={runs}
                    keyExtractor={(item, index) => item.run_id || item.id || String(index)}
                    renderItem={renderItem}
                    contentContainerStyle={styles.listContainer}
                    refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#fff" />}
                    ListEmptyComponent={
                        <Text style={styles.emptyText}>No quantum jobs found.</Text>
                    }
                />
            )}
        </SafeAreaView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#0f172a', // slate-900
    },
    header: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 20,
        backgroundColor: '#1e293b', // slate-800
        borderBottomWidth: 1,
        borderBottomColor: '#334155', // slate-700
    },
    runButton: {
        backgroundColor: '#3b82f6',
        paddingHorizontal: 16,
        paddingVertical: 10,
        borderRadius: 8,
    },
    runButtonText: {
        color: '#ffffff',
        fontWeight: 'bold',
        fontSize: 14,
    },
    headerTitle: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#f8fafc', // slate-50
        letterSpacing: 0.5,
    },
    headerSubtitle: {
        fontSize: 14,
        color: '#94a3b8', // slate-400
        marginTop: 4,
    },
    errorContainer: {
        backgroundColor: '#ef444420',
        padding: 12,
        marginHorizontal: 16,
        marginTop: 16,
        borderRadius: 8,
        borderWidth: 1,
        borderColor: '#ef444440',
    },
    errorText: {
        color: '#fca5a5',
        fontSize: 13,
        textAlign: 'center',
    },
    loaderContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
    },
    loaderText: {
        color: '#94a3b8',
        marginTop: 16,
        fontSize: 16,
    },
    listContainer: {
        padding: 16,
    },
    card: {
        backgroundColor: '#1e293b', // slate-800
        borderRadius: 12,
        padding: 16,
        marginBottom: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.2,
        shadowRadius: 4,
        elevation: 3,
        borderWidth: 1,
        borderColor: '#334155', // slate-700
    },
    cardHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 12,
    },
    circuitName: {
        fontSize: 18,
        fontWeight: '600',
        color: '#f1f5f9', // slate-100
        flex: 1,
        marginRight: 10,
    },
    badge: {
        paddingHorizontal: 10,
        paddingVertical: 4,
        borderRadius: 12,
    },
    badgeText: {
        fontSize: 11,
        fontWeight: 'bold',
        textTransform: 'uppercase',
    },
    cardBody: {
        borderTopWidth: 1,
        borderTopColor: '#334155',
        paddingTop: 12,
    },
    detailText: {
        color: '#94a3b8', // slate-400
        fontSize: 14,
        marginBottom: 4,
    },
    emptyText: {
        color: '#64748b', // slate-500
        textAlign: 'center',
        marginTop: 40,
        fontSize: 16,
    }
});
