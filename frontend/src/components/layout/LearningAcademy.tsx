/* Milimo Quantum — Learning Academy Component */
import { useState, useEffect, useCallback } from 'react';
import { fetchWithAuth } from '../../services/api';

interface LessonSummary {
    id: string;
    title: string;
    icon: string;
    description: string;
    difficulty: string;
    estimated_minutes: number;
    order: number;
    completed: boolean;
    quiz_score: number | null;
}

interface Section {
    type: 'text' | 'code' | 'quiz';
    content?: string;
    title?: string;
    description?: string;
    code?: string;
    question?: string;
    options?: string[];
    correct?: number;
    explanation?: string;
}

interface Lesson extends LessonSummary {
    sections: Section[];
}

export function LearningAcademy({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
    const [lessons, setLessons] = useState<LessonSummary[]>([]);
    const [activeLesson, setActiveLesson] = useState<Lesson | null>(null);
    const [loading, setLoading] = useState(true);
    const [quizAnswers, setQuizAnswers] = useState<Record<number, number>>({});
    const [showExplanation, setShowExplanation] = useState<Record<number, boolean>>({});

    useEffect(() => {
        if (!isOpen) return;
        setLoading(true);
        fetchWithAuth('/api/academy/lessons')
            .then(r => r.json())
            .then(data => setLessons(data.lessons || []))
            .catch(() => { })
            .finally(() => setLoading(false));
    }, [isOpen]);

    const openLesson = useCallback((id: string) => {
        fetchWithAuth(`/api/academy/lessons/${id}`)
            .then(r => r.json())
            .then(data => {
                setActiveLesson(data);
                setQuizAnswers({});
                setShowExplanation({});
            })
            .catch(() => { });
    }, []);

    const handleQuizAnswer = useCallback((sectionIdx: number, answerIdx: number) => {
        setQuizAnswers(prev => ({ ...prev, [sectionIdx]: answerIdx }));
        setShowExplanation(prev => ({ ...prev, [sectionIdx]: true }));
    }, []);

    const markComplete = useCallback(async () => {
        if (!activeLesson) return;

        // Calculate quiz score from answers
        const quizSections = activeLesson.sections
            .map((s, idx) => ({ ...s, idx }))
            .filter(s => s.type === 'quiz');
        let quizScore: number | undefined;
        if (quizSections.length > 0) {
            const correct = quizSections.filter(s => quizAnswers[s.idx] === s.correct).length;
            quizScore = Math.round((correct / quizSections.length) * 100);
        }

        await fetchWithAuth(`/api/academy/progress?lesson_id=${activeLesson.id}&completed=true${quizScore !== undefined ? `&quiz_score=${quizScore}` : ''}`, {
            method: 'POST',
        });
        setLessons(prev => prev.map(l =>
            l.id === activeLesson.id ? { ...l, completed: true, quiz_score: quizScore ?? null } : l
        ));
        setActiveLesson(prev => prev ? { ...prev, completed: true, quiz_score: quizScore ?? null } : null);
    }, [activeLesson, quizAnswers]);

    const runCode = useCallback((code: string) => {
        // Send code to chat as a message that triggers sandbox execution
        const event = new CustomEvent('academy-run-code', { detail: { code } });
        window.dispatchEvent(event);
    }, []);

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex bg-black/60 backdrop-blur-sm">
            <div className="bg-[#0d1117] border border-cyan-500/20 rounded-2xl shadow-2xl
                w-full max-w-5xl max-h-[90vh] overflow-hidden mx-auto my-6 flex">

                {/* Sidebar — Lesson List */}
                <div className="w-72 border-r border-white/[0.06] flex flex-col">
                    <div className="px-5 py-4 border-b border-white/[0.06] flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <span className="text-xl">🎓</span>
                            <h2 className="text-base font-semibold text-white">Academy</h2>
                        </div>
                        <button onClick={onClose}
                            className="w-7 h-7 rounded-lg bg-white/5 hover:bg-white/10
                                flex items-center justify-center text-gray-400 hover:text-white
                                transition-all cursor-pointer text-sm">✕</button>
                    </div>

                    <div className="flex-1 overflow-y-auto p-3 space-y-1">
                        {loading ? (
                            <div className="flex items-center justify-center py-8 text-gray-500 text-sm">
                                Loading...
                            </div>
                        ) : (
                            lessons.map(lesson => (
                                <button key={lesson.id}
                                    onClick={() => openLesson(lesson.id)}
                                    className={`w-full text-left px-3 py-2.5 rounded-xl transition-all cursor-pointer
                                        ${activeLesson?.id === lesson.id
                                            ? 'bg-cyan-500/10 border border-cyan-500/30'
                                            : 'hover:bg-white/[0.04] border border-transparent'
                                        }`}>
                                    <div className="flex items-center gap-2">
                                        <span className="text-lg">{lesson.icon}</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="text-sm font-medium text-gray-200 truncate flex items-center gap-1.5">
                                                {lesson.title}
                                                {lesson.completed && <span className="text-green-400 text-xs">✓</span>}
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                {lesson.difficulty} · {lesson.estimated_minutes} min
                                            </div>
                                        </div>
                                    </div>
                                </button>
                            ))
                        )}
                    </div>

                    {/* Progress */}
                    <div className="px-4 py-3 border-t border-white/[0.06]">
                        <div className="flex items-center justify-between text-xs text-gray-500 mb-1.5">
                            <span>Progress</span>
                            <span>{lessons.filter(l => l.completed).length}/{lessons.length}</span>
                        </div>
                        <div className="h-1.5 bg-white/[0.06] rounded-full overflow-hidden">
                            <div className="h-full bg-gradient-to-r from-cyan-500 to-blue-500 rounded-full transition-all duration-500"
                                style={{ width: `${lessons.length ? (lessons.filter(l => l.completed).length / lessons.length) * 100 : 0}%` }} />
                        </div>
                    </div>
                </div>

                {/* Main Content — Lesson Viewer */}
                <div className="flex-1 overflow-y-auto">
                    {activeLesson ? (
                        <div className="p-8">
                            {/* Header */}
                            <div className="mb-8">
                                <div className="flex items-center gap-3 mb-2">
                                    <span className="text-3xl">{activeLesson.icon}</span>
                                    <h1 className="text-2xl font-bold text-white">{activeLesson.title}</h1>
                                    {activeLesson.completed && (
                                        <span className="px-2 py-0.5 text-xs rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
                                            Completed
                                        </span>
                                    )}
                                </div>
                                <p className="text-gray-400 text-sm">{activeLesson.description}</p>
                            </div>

                            {/* Sections */}
                            <div className="space-y-8">
                                {activeLesson.sections.map((section, idx) => (
                                    <div key={idx}>
                                        {section.type === 'text' && (
                                            <div className="prose prose-invert prose-sm max-w-none
                                                [&_h2]:text-xl [&_h2]:font-bold [&_h2]:text-white [&_h2]:mb-3
                                                [&_h3]:text-lg [&_h3]:font-semibold [&_h3]:text-gray-200
                                                [&_p]:text-gray-300 [&_p]:leading-relaxed
                                                [&_table]:w-full [&_th]:text-left [&_th]:text-gray-400 [&_th]:text-xs [&_th]:uppercase
                                                [&_td]:py-1.5 [&_td]:text-sm [&_td]:text-gray-300
                                                [&_code]:bg-cyan-500/10 [&_code]:text-cyan-300 [&_code]:px-1.5 [&_code]:rounded
                                                [&_strong]:text-white">
                                                {section.content?.split('\n').map((line, i) => {
                                                    if (line.startsWith('## ')) return <h2 key={i}>{line.replace('## ', '')}</h2>;
                                                    if (line.startsWith('### ')) return <h3 key={i}>{line.replace('### ', '')}</h3>;
                                                    if (line.startsWith('$$') && line.endsWith('$$')) {
                                                        return <div key={i} className="text-center py-2 text-cyan-300 font-mono text-sm bg-white/[0.02] rounded-lg px-4 my-2">{line}</div>;
                                                    }
                                                    if (line.startsWith('|')) {
                                                        return <div key={i} className="text-sm text-gray-300 font-mono">{line}</div>;
                                                    }
                                                    if (line.startsWith('- ') || line.startsWith('* ')) {
                                                        return <div key={i} className="pl-4 text-gray-300 text-sm">• {line.slice(2)}</div>;
                                                    }
                                                    if (line.trim() === '') return <br key={i} />;
                                                    return <p key={i} className="text-gray-300 text-sm leading-relaxed">{line}</p>;
                                                })}
                                            </div>
                                        )}

                                        {section.type === 'code' && (
                                            <div className="bg-white/[0.02] border border-cyan-500/10 rounded-xl overflow-hidden">
                                                <div className="px-4 py-3 border-b border-white/[0.06] flex items-center justify-between">
                                                    <div>
                                                        <div className="text-sm font-medium text-cyan-400">{section.title}</div>
                                                        <div className="text-xs text-gray-500 mt-0.5">{section.description}</div>
                                                    </div>
                                                    <button onClick={() => runCode(section.code || '')}
                                                        className="px-3 py-1.5 rounded-lg text-xs font-medium
                                                            bg-cyan-500/10 text-cyan-400 border border-cyan-500/20
                                                            hover:bg-cyan-500/20 transition-all cursor-pointer">
                                                        ▶ Run Code
                                                    </button>
                                                </div>
                                                <pre className="p-4 overflow-x-auto text-xs leading-relaxed">
                                                    <code className="text-gray-300">{section.code}</code>
                                                </pre>
                                            </div>
                                        )}

                                        {section.type === 'quiz' && (
                                            <div className="bg-white/[0.02] border border-purple-500/10 rounded-xl p-5">
                                                <div className="text-sm font-medium text-purple-400 mb-3">
                                                    🧠 Quiz: {section.question}
                                                </div>
                                                <div className="space-y-2">
                                                    {section.options?.map((opt, optIdx) => {
                                                        const answered = quizAnswers[idx] !== undefined;
                                                        const isSelected = quizAnswers[idx] === optIdx;
                                                        const isCorrect = optIdx === section.correct;
                                                        let style = 'border-white/[0.06] hover:border-purple-500/30';
                                                        if (answered && isCorrect) style = 'border-green-500/40 bg-green-500/5';
                                                        if (answered && isSelected && !isCorrect) style = 'border-red-500/40 bg-red-500/5';

                                                        return (
                                                            <button key={optIdx}
                                                                onClick={() => !answered && handleQuizAnswer(idx, optIdx)}
                                                                disabled={answered}
                                                                className={`w-full text-left px-4 py-2.5 rounded-lg border
                                                                    text-sm text-gray-300 transition-all
                                                                    ${answered ? '' : 'cursor-pointer'}
                                                                    ${style}`}>
                                                                <span className="text-gray-500 mr-2">{String.fromCharCode(65 + optIdx)}.</span>
                                                                {opt}
                                                                {answered && isCorrect && <span className="ml-2 text-green-400">✓</span>}
                                                                {answered && isSelected && !isCorrect && <span className="ml-2 text-red-400">✗</span>}
                                                            </button>
                                                        );
                                                    })}
                                                </div>
                                                {showExplanation[idx] && section.explanation && (
                                                    <div className="mt-3 px-4 py-2.5 bg-white/[0.02] rounded-lg text-xs text-gray-400 border border-white/[0.04]">
                                                        💡 {section.explanation}
                                                    </div>
                                                )}
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>

                            {/* Mark Complete Button */}
                            {!activeLesson.completed && (
                                <div className="mt-8 flex justify-center">
                                    <button onClick={markComplete}
                                        className="px-6 py-2.5 rounded-xl text-sm font-medium
                                            bg-gradient-to-r from-cyan-500 to-blue-500 text-white
                                            hover:from-cyan-400 hover:to-blue-400
                                            transition-all cursor-pointer shadow-lg shadow-cyan-500/20">
                                        ✓ Mark as Complete
                                    </button>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500">
                            <div className="text-5xl mb-4">🎓</div>
                            <p className="text-lg font-medium text-gray-300">Quantum Learning Academy</p>
                            <p className="text-sm mt-1">Select a lesson from the sidebar to begin</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
