import React, { useState } from 'react';

interface Lesson {
    id: string;
    title: string;
    difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
    status: 'locked' | 'available' | 'completed';
    description: string;
}

export const AcademyPanel: React.FC<{ isOpen: boolean; onClose: () => void }> = ({ isOpen, onClose }) => {
    const [lessons, setLessons] = useState<Lesson[]>([
        { id: '1', title: 'Qubits & Superposition', difficulty: 'Beginner', status: 'completed', description: 'Master the basics of quantum states and the Hadamard gate.' },
        { id: '2', title: 'Entanglement & Bell States', difficulty: 'Beginner', status: 'completed', description: 'Create your first entangled pair using CNOT gates.' },
        { id: '3', title: 'Quantum Teleportation', difficulty: 'Intermediate', status: 'available', description: 'Transmit quantum information across arbitrary distances.' },
        { id: '4', title: 'Shor\'s Algorithm', difficulty: 'Advanced', status: 'locked', description: 'Large-scale integer factorization via period finding.' },
    ]);

    const [isGrading, setIsGrading] = useState(false);
    const [gradingResult, setGradingResult] = useState<string | null>(null);

    const handleVerify = (lessonId: string) => {
        setIsGrading(true);
        setGradingResult(null);

        // Simulate backend verification of the circuit
        setTimeout(() => {
            setIsGrading(false);
            setGradingResult('Success! State vector matches theoretical prediction (Fidelity: 0.9998)');

            // Mark as completed
            setLessons(prev => prev.map(l =>
                l.id === lessonId ? { ...l, status: 'completed' } : l
            ));
        }, 2500);
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-[#0b0e14] border border-cyan-500/20 rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col overflow-hidden shadow-2xl">
                {/* Header */}
                <div className="px-6 py-5 border-b border-cyan-500/10 flex items-center justify-between bg-[#0d1117]">
                    <div className="flex items-center gap-4">
                        <div className="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center text-2xl border border-cyan-500/20">🎓</div>
                        <div>
                            <h3 className="text-xl font-bold text-white">Quantum Academy</h3>
                            <p className="text-xs text-gray-400 mt-1">Interactive research-grade curriculum and automated grading</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/5 rounded-lg text-gray-400 transition-colors">✕</button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 bg-[#05070a]">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {lessons.map((lesson) => (
                            <div
                                key={lesson.id}
                                className={`p-5 rounded-2xl border transition-all duration-300 relative group overflow-hidden ${lesson.status === 'locked'
                                    ? 'border-white/5 bg-white/2 opacity-60'
                                    : 'border-cyan-500/20 bg-[#0d1117] hover:border-cyan-500/40 hover:shadow-[0_0_20px_rgba(34,211,238,0.05)]'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${lesson.difficulty === 'Beginner' ? 'bg-green-500/10 text-green-400 border border-green-500/20' :
                                        lesson.difficulty === 'Intermediate' ? 'bg-yellow-500/10 text-yellow-400 border border-yellow-500/20' :
                                            'bg-red-500/10 text-red-400 border border-red-500/20'
                                        }`}>
                                        {lesson.difficulty}
                                    </span>
                                    <span className="text-xs font-medium text-gray-500">
                                        {lesson.status === 'completed' && '✅ Completed'}
                                        {lesson.status === 'available' && '▶️ Start Lesson'}
                                        {lesson.status === 'locked' && '🔒 Locked'}
                                    </span>
                                </div>

                                <h4 className="text-lg font-bold text-white mb-2 group-hover:text-cyan-400 transition-colors">{lesson.title}</h4>
                                <p className="text-sm text-gray-400 leading-relaxed mb-6">{lesson.description}</p>

                                <button
                                    disabled={lesson.status === 'locked' || (isGrading && lesson.status === 'available')}
                                    onClick={() => lesson.status === 'available' && handleVerify(lesson.id)}
                                    className={`w-full py-2.5 rounded-xl font-bold text-sm transition-all ${lesson.status === 'completed'
                                        ? 'bg-white/5 text-gray-300 hover:bg-white/10'
                                        : lesson.status === 'available'
                                            ? 'bg-cyan-500 text-black hover:bg-cyan-400 shadow-[0_0_15px_rgba(34,211,238,0.2)]'
                                            : 'bg-white/5 text-gray-600 cursor-not-allowed'
                                        }`}
                                >
                                    {isGrading && lesson.status === 'available' ? (
                                        <div className="flex items-center justify-center gap-2">
                                            <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
                                            Grading Circuit...
                                        </div>
                                    ) : lesson.status === 'completed' ? 'Review Lesson' : 'Verify Circuit'}
                                </button>

                                {gradingResult && lesson.status === 'completed' && (
                                    <div className="mt-3 p-2 rounded bg-green-500/10 border border-green-500/20 text-[10px] text-green-400 font-mono animate-fade-in">
                                        {gradingResult}
                                    </div>
                                )}

                                {/* Progress Bar for active cards */}
                                {lesson.status === 'available' && (
                                    <div className="absolute bottom-0 left-0 h-1 bg-cyan-500/30 w-full">
                                        <div className="h-full bg-cyan-500 w-[15%]" />
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-cyan-500/10 bg-[#0d1117] flex justify-between items-center">
                    <div className="flex gap-4">
                        <div className="text-center">
                            <div className="text-lg font-bold text-white">2/12</div>
                            <div className="text-[10px] text-gray-500 uppercase font-bold">Lessons</div>
                        </div>
                        <div className="text-center">
                            <div className="text-lg font-bold text-cyan-400">1,450</div>
                            <div className="text-[10px] text-gray-500 uppercase font-bold">XP</div>
                        </div>
                    </div>
                    <button className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/5 rounded-lg text-sm font-medium text-gray-300 transition-all">
                        View Certificate
                    </button>
                </div>
            </div>
        </div>
    );
};
