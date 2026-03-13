
import React, { useState, useRef, useEffect, useCallback, useReducer } from 'react';
import { Agent, AgentName, AgentStatus, Message, ResultData, Molecule, AdmetProperty } from './types';
// Fix: Import decode and createBlob directly to avoid scoping issues.
import { runFullWorkflow, runRefinementWorkflow, determineIntent, runChat, Intent, startVoiceConversation, decodeAudioData, runHypothesisOnTranscript, decode, createBlob } from './services/geminiService';
import { LiveServerMessage } from '@google/genai';
import MoleculeViewer from './components/MoleculeViewer';
import MoleculeViewer3D from './components/MoleculeViewer3D';
import CandidateComparisonChart from './components/CandidateComparisonChart';
import KnowledgeGraph from './components/KnowledgeGraph';
import { UserIcon, SendIcon, MicIcon, LoaderIcon, CheckCircleIcon, XCircleIcon, BeakerIcon, BookOpenIcon, AtomIcon, ZapIcon, ListChecksIcon, Share2Icon, ClipboardListIcon, MilimoLogoIcon, FlaskConicalIcon, CrosshairIcon, BarChartIcon, NetworkIcon, LightbulbIcon, AlertTriangleIcon, FileIcon, DownloadIcon, HistoryIcon, PlusCircleIcon, StopCircleIcon } from './components/Icons';
import ReactMarkdown from 'react-markdown';
import Test3DPage from './components/Test3DPage';

// --- State Management (Phase 3 Refactor) ---

type AppState = {
    agents: Agent[];
    messages: Message[];
    isLoading: boolean;
    resultData: ResultData | null;
    activeTab: ResultTab;
    selectedMolecule: Molecule | null;
    uploadedFile: { name: string; content: string } | null;
    history: Session[];
    activeSessionId: string;
    voiceSessionStatus: 'inactive' | 'connecting' | 'active' | 'error';
    isAiSpeaking: boolean;
};

type Action =
    | { type: 'START_WORKFLOW'; payload: { userMessage: Message; currentInput: string } }
    | { type: 'START_REFINEMENT'; payload: { userMessage: Message; currentInput: string } }
    | { type: 'START_CHAT'; payload: Message }
    | { type: 'CHAT_COMPLETE'; payload: Message }
    | { type: 'WORKFLOW_COMPLETE'; payload: { results: ResultData; aiMessage: Message } }
    | { type: 'WORKFLOW_ERROR'; payload: Message }
    | { type: 'SET_AGENTS'; payload: Agent[] }
    | { type: 'UPDATE_AGENT_STATUS'; payload: { agentName: AgentName; status: AgentStatus; message: string } }
    | { type: 'SET_INPUT_VALUE'; payload: string }
    | { type: 'SET_UPLOADED_FILE'; payload: { name: string; content: string } | null }
    | { type: 'SET_ACTIVE_TAB'; payload: ResultTab }
    | { type: 'SET_SELECTED_MOLECULE'; payload: Molecule | null }
    | { type: 'LOAD_HISTORY'; payload: Session[] }
    | { type: 'SAVE_SESSION'; payload: { results: ResultData; finalMessages: Message[]; finalAgents: Agent[] } }
    | { type: 'SELECT_HISTORY_SESSION'; payload: Session }
    | { type: 'NEW_SESSION' }
    | { type: 'START_VOICE_SESSION' }
    | { type: 'VOICE_SESSION_ACTIVE' }
    | { type: 'VOICE_SESSION_CLOSED' }
    | { type: 'SET_AI_SPEAKING_STATUS'; payload: boolean }
    | { type: 'ADD_TRANSCRIPT_TO_HISTORY'; payload: string };


const initialAgents: Agent[] = [
  { name: AgentName.TARGET_IDENTIFICATION, status: AgentStatus.IDLE, description: "Identifies protein target from prompt.", message: "Awaiting workflow..." },
  { name: AgentName.LITERATURE, status: AgentStatus.IDLE, description: "Scans scientific literature for insights.", message: "Awaiting workflow..." },
  { name: AgentName.MOLECULAR_DESIGN, status: AgentStatus.IDLE, description: "Generates novel molecular structures.", message: "Awaiting workflow..." },
  { name: AgentName.PROPERTY_PREDICTION, status: AgentStatus.IDLE, description: "Predicts ADMET properties of molecules.", message: "Awaiting workflow..." },
  { name: AgentName.QUANTUM_SIMULATION, status: AgentStatus.IDLE, description: "Simulates molecular binding energy.", message: "Awaiting workflow..." },
  { name: AgentName.SYNTHESIZABILITY, status: AgentStatus.IDLE, description: "Calculates synthetic accessibility score.", message: "Awaiting workflow..." },
  { name: AgentName.INTERACTION_ANALYSIS, status: AgentStatus.IDLE, description: "Analyzes ligand-protein interactions.", message: "Awaiting workflow..." },
  { name: AgentName.RETROSYNTHESIS, status: AgentStatus.IDLE, description: "Predicts chemical synthesis pathway.", message: "Awaiting workflow..." },
  { name: AgentName.EXPERIMENTAL_PLANNER, status: AgentStatus.IDLE, description: "Designs validation experiments.", message: "Awaiting workflow..." },
  { name: AgentName.KNOWLEDGE_GRAPH, status: AgentStatus.IDLE, description: "Integrates findings into a knowledge base.", message: "Awaiting workflow..." },
  { name: AgentName.FAILURE_ANALYSIS, status: AgentStatus.IDLE, description: "Analyzes workflow failures and suggests fixes.", message: "Awaiting workflow..." },
  { name: AgentName.HYPOTHESIS, status: AgentStatus.IDLE, description: "Generates proactive next steps.", message: "Awaiting workflow..." },
];

const refinementAgents: AgentName[] = [
    AgentName.MOLECULAR_DESIGN,
    AgentName.PROPERTY_PREDICTION,
    AgentName.QUANTUM_SIMULATION,
    AgentName.SYNTHESIZABILITY,
    AgentName.INTERACTION_ANALYSIS,
    AgentName.RETROSYNTHESIS,
    AgentName.EXPERIMENTAL_PLANNER,
    AgentName.KNOWLEDGE_GRAPH,
    AgentName.HYPOTHESIS,
];

const initialState: AppState = {
    agents: initialAgents,
    messages: [
        {
            id: 'init',
            sender: 'ai',
            text: "Welcome to the Milimo Quantum Drug Discovery Workspace. Describe your research goal to begin. For example: 'Design a novel, non-toxic inhibitor for BRAF V600E in melanoma.'"
        }
    ],
    isLoading: false,
    resultData: null,
    activeTab: 'summary',
    selectedMolecule: null,
    uploadedFile: null,
    history: [],
    activeSessionId: `session-${Date.now()}`,
    voiceSessionStatus: 'inactive',
    isAiSpeaking: false,
};

const appReducer = (state: AppState, action: Action): AppState => {
    switch (action.type) {
        case 'START_WORKFLOW':
            return {
                ...state,
                messages: [...state.messages, action.payload.userMessage],
                isLoading: true,
                resultData: null,
                activeTab: 'summary',
                agents: initialAgents.map(a => ({ ...a, status: AgentStatus.IDLE, message: 'Queued' })),
            };
        case 'START_REFINEMENT':
             return {
                ...state,
                messages: [...state.messages, action.payload.userMessage],
                isLoading: true,
                agents: initialAgents.map(a => 
                    refinementAgents.includes(a.name) 
                        ? { ...a, status: AgentStatus.IDLE, message: 'Queued' } 
                        : { ...a, status: AgentStatus.IDLE, message: 'Not in this workflow' }
                )
            };
        case 'START_CHAT':
            return {
                ...state,
                messages: [...state.messages, action.payload],
                isLoading: true,
            };
        case 'CHAT_COMPLETE':
            return {
                ...state,
                isLoading: false,
                messages: [...state.messages, action.payload],
            };
        case 'WORKFLOW_COMPLETE':
            const leadMolecule = action.payload.results.molecules[0] || null;
            return {
                ...state,
                isLoading: false,
                resultData: action.payload.results,
                messages: [...state.messages, action.payload.aiMessage],
                selectedMolecule: leadMolecule,
            };
        case 'WORKFLOW_ERROR':
             return {
                ...state,
                isLoading: false,
                messages: [...state.messages, action.payload],
            };
        case 'SET_AGENTS':
            return { ...state, agents: action.payload };
        case 'UPDATE_AGENT_STATUS': {
             // Fix: Removed the logic that added spinner messages to the chat history.
             // The agent panel is the single source of truth for agent status.
             return {
                ...state,
                agents: state.agents.map(agent =>
                    agent.name === action.payload.agentName 
                        ? { ...agent, status: action.payload.status, message: action.payload.message } 
                        : agent
                ),
            };
        }
        case 'SET_UPLOADED_FILE':
            return { ...state, uploadedFile: action.payload };
        case 'SET_ACTIVE_TAB':
            return { ...state, activeTab: action.payload };
        case 'SET_SELECTED_MOLECULE':
             return { ...state, selectedMolecule: action.payload };
        case 'LOAD_HISTORY':
            return { ...state, history: action.payload };
        case 'SAVE_SESSION':
            const { results, finalMessages, finalAgents } = action.payload;
            const sessionName = finalMessages.find(m => m.sender === 'user')?.text.substring(0, 50) || 'Untitled Session';
            const newSession: Session = {
                id: state.activeSessionId,
                name: sessionName,
                timestamp: Date.now(),
                messages: finalMessages,
                resultData: results,
                agents: finalAgents,
            };
            const existingIndex = state.history.findIndex(s => s.id === state.activeSessionId);
            let updatedHistory: Session[];
            if (existingIndex > -1) {
                updatedHistory = [...state.history];
                updatedHistory[existingIndex] = newSession;
            } else {
                updatedHistory = [newSession, ...state.history];
            }
             try {
                localStorage.setItem('mqdd_history', JSON.stringify(updatedHistory));
            } catch (error) {
                console.error("Failed to save history to localStorage", error);
            }
            return { ...state, history: updatedHistory };
        case 'SELECT_HISTORY_SESSION':
            return {
                ...state,
                agents: action.payload.agents,
                messages: action.payload.messages,
                resultData: action.payload.resultData,
                selectedMolecule: action.payload.resultData?.molecules[0] || null,
                activeSessionId: action.payload.id,
                activeTab: 'summary',
                voiceSessionStatus: 'inactive',
                isAiSpeaking: false,
            };
        case 'NEW_SESSION':
            return {
                ...initialState,
                history: state.history, // Keep history
                activeSessionId: `session-${Date.now()}`,
            };
        case 'START_VOICE_SESSION':
            return { ...state, voiceSessionStatus: 'connecting' };
        case 'VOICE_SESSION_ACTIVE':
            return { ...state, voiceSessionStatus: 'active' };
        case 'VOICE_SESSION_CLOSED':
            return { ...state, voiceSessionStatus: 'inactive', isAiSpeaking: false };
        case 'SET_AI_SPEAKING_STATUS':
            return { ...state, isAiSpeaking: action.payload };
        case 'ADD_TRANSCRIPT_TO_HISTORY':
            const transcriptMessage: Message = {
                id: `transcript-${Date.now()}`,
                sender: 'system',
                text: action.payload
            };
            return {
                ...state,
                messages: [...state.messages, transcriptMessage],
            };
        default:
            return state;
    }
};

type ResultTab = 'summary' | 'candidate' | 'analysis' | 'synthesis' | 'plan' | 'knowledge' | 'literature';

interface Session {
    id: string;
    name: string;
    timestamp: number;
    messages: Message[];
    resultData: ResultData;
    agents: Agent[];
}

// Custom hook to get the previous value of a prop/state
function usePrevious<T>(value: T): T | undefined {
  const ref = useRef<T>();
  // Fix: Added a dependency array to `useEffect`. The original implementation was missing it,
  // causing the hook to run on every render. This change ensures the effect only runs when the
  // `value` prop changes, which is the correct and more performant behavior for a `usePrevious` hook.
  useEffect(() => {
    ref.current = value;
  }, [value]);
  return ref.current;
}


const App: React.FC = () => {
    const [state, dispatch] = useReducer(appReducer, initialState);
    const { agents, messages, isLoading, resultData, activeTab, selectedMolecule, uploadedFile, history, activeSessionId, voiceSessionStatus, isAiSpeaking } = state;
    
    const [view, setView] = useState<'main' | 'test'>('main');
    const [inputValue, setInputValue] = useState('');
    const [isExportMenuOpen, setIsExportMenuOpen] = useState(false);
    const [activeTabKey, setActiveTabKey] = useState(Date.now()); // For animation trigger
    const [voiceTrigger, setVoiceTrigger] = useState(0);

    const mainContentRef = useRef<HTMLDivElement>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const recognitionRef = useRef<any>(null); // For speech recognition
    const [isListening, setIsListening] = useState(false);
    
    // Refs for all voice session resources to persist them across re-renders
    const sessionRef = useRef<any>(null);
    const mediaStreamRef = useRef<MediaStream | null>(null);
    const inputAudioContextRef = useRef<AudioContext | null>(null);
    const scriptProcessorRef = useRef<ScriptProcessorNode | null>(null);
    const outputAudioContextRef = useRef<AudioContext | null>(null);
    const audioSourcesRef = useRef<Set<AudioBufferSourceNode>>(new Set());
    const nextAudioStartTimeRef = useRef<number>(0);
    // Ref to store transcription data without causing re-renders
    const transcriptionRef = useRef({ userInput: '', modelOutput: '' });
    
    // Get the previous value of voiceSessionStatus to detect transitions
    const prevVoiceStatus = usePrevious(voiceSessionStatus);

    const updateAgentStatus = useCallback((agentName: AgentName, status: AgentStatus, message: string) => {
        dispatch({ type: 'UPDATE_AGENT_STATUS', payload: { agentName, status, message } });
    }, []);

    useEffect(() => {
        mainContentRef.current?.scrollTo({ top: mainContentRef.current.scrollHeight, behavior: 'smooth' });
    }, [messages, isLoading]);

    useEffect(() => {
        if (resultData && resultData.molecules.length > 0 && !selectedMolecule) {
             dispatch({ type: 'SET_SELECTED_MOLECULE', payload: resultData.molecules[0] });
        }
    }, [resultData, selectedMolecule]);

    useEffect(() => {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (SpeechRecognition) {
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.interimResults = false;
            recognitionRef.current.lang = 'en-US';

            recognitionRef.current.onresult = (event: any) => {
                const transcript = event.results[0][0].transcript;
                setInputValue(transcript);
                setIsListening(false);
            };

            recognitionRef.current.onerror = (event: any) => {
                console.error('Speech recognition error:', event.error);
                setIsListening(false);
            };

            recognitionRef.current.onend = () => {
                setIsListening(false);
            };
        }
    }, []);
    
    // Effect for managing the voice conversation lifecycle, triggered by `voiceTrigger`
    useEffect(() => {
        if (voiceTrigger === 0 || !resultData) {
            return;
        }

        let isEffectCancelled = false;
        
        // Reset transcript ref at the start of a new session
        transcriptionRef.current = { userInput: '', modelOutput: '' };

        const setupAndRunVoiceSession = async () => {
            try {
                // Fix: Get only sessionPromise from startVoiceConversation.
                // decode and createBlob are now imported.
                const { sessionPromise } = startVoiceConversation(resultData, {
                    onopen: () => {
                        if (isEffectCancelled) return;
                        dispatch({ type: 'VOICE_SESSION_ACTIVE' });
                    },
                    onmessage: async (message: LiveServerMessage) => {
                        if (isEffectCancelled) return;
                        // Store transcription in ref instead of state to prevent re-renders
                        if (message.serverContent?.inputTranscription) {
                            transcriptionRef.current.userInput += message.serverContent.inputTranscription.text;
                        } else if (message.serverContent?.outputTranscription) {
                            transcriptionRef.current.modelOutput += message.serverContent.outputTranscription.text;
                        }
                        
                        const base64Audio = message.serverContent?.modelTurn?.parts[0]?.inlineData?.data;
                        if (base64Audio) {
                            if (!outputAudioContextRef.current || outputAudioContextRef.current.state === 'closed') {
                                outputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 24000 });
                            }
                            const ctx = outputAudioContextRef.current;
                            dispatch({ type: 'SET_AI_SPEAKING_STATUS', payload: true });
                            
                            nextAudioStartTimeRef.current = Math.max(nextAudioStartTimeRef.current, ctx.currentTime);
                            const audioBuffer = await decodeAudioData(decode(base64Audio), ctx, 24000, 1);
                            const source = ctx.createBufferSource();
                            source.buffer = audioBuffer;
                            source.connect(ctx.destination);
                            
                            source.addEventListener('ended', () => {
                                audioSourcesRef.current.delete(source);
                                if (audioSourcesRef.current.size === 0) {
                                    dispatch({ type: 'SET_AI_SPEAKING_STATUS', payload: false });
                                }
                            });
                            
                            source.start(nextAudioStartTimeRef.current);
                            nextAudioStartTimeRef.current += audioBuffer.duration;
                            audioSourcesRef.current.add(source);
                        }
                        
                        if (message.serverContent?.interrupted) {
                            audioSourcesRef.current.forEach(s => s.stop());
                            audioSourcesRef.current.clear();
                            nextAudioStartTimeRef.current = 0;
                            dispatch({ type: 'SET_AI_SPEAKING_STATUS', payload: false });
                        }
                    },
                    onerror: (e: ErrorEvent) => {
                        console.error("Voice session error:", e);
                        // onclose will be called automatically after an error.
                    },
                    onclose: () => {
                        // This is the single source of truth for the session ending.
                        // It resets the application state. The useEffect's cleanup function
                        // handles releasing the hardware/browser resources.
                        if (!isEffectCancelled) {
                             dispatch({ type: 'VOICE_SESSION_CLOSED' });
                        }
                    },
                });

                sessionRef.current = await sessionPromise;
                if (isEffectCancelled) {
                    sessionRef.current?.close();
                    return;
                }

                mediaStreamRef.current = await navigator.mediaDevices.getUserMedia({ audio: true });
                if (isEffectCancelled) {
                    mediaStreamRef.current.getTracks().forEach(track => track.stop());
                    return;
                }

                inputAudioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)({ sampleRate: 16000 });
                const source = inputAudioContextRef.current.createMediaStreamSource(mediaStreamRef.current);
                scriptProcessorRef.current = inputAudioContextRef.current.createScriptProcessor(4096, 1, 1);

                scriptProcessorRef.current.onaudioprocess = (audioProcessingEvent) => {
                    const inputData = audioProcessingEvent.inputBuffer.getChannelData(0);
                    const pcmBlob = createBlob(inputData);
                    // Fix: Use sessionPromise.then() to send data, as per Gemini API guidelines, to prevent race conditions.
                    sessionPromise.then((session) => {
                        session.sendRealtimeInput({ media: pcmBlob });
                    });
                };
                
                source.connect(scriptProcessorRef.current);
                scriptProcessorRef.current.connect(inputAudioContextRef.current.destination);
            } catch (err) {
                if (!isEffectCancelled) {
                    console.error("Voice session setup failed:", err);
                    dispatch({ type: 'VOICE_SESSION_CLOSED' });
                }
            }
        };

        setupAndRunVoiceSession();

        return () => {
            isEffectCancelled = true;
            // This is the resource cleanup function.
            sessionRef.current?.close();
            sessionRef.current = null;
            
            mediaStreamRef.current?.getTracks().forEach(track => track.stop());
            mediaStreamRef.current = null;
            
            scriptProcessorRef.current?.disconnect();
            scriptProcessorRef.current = null;
            
            inputAudioContextRef.current?.close().catch(console.error);
            inputAudioContextRef.current = null;

            audioSourcesRef.current.forEach(source => source.stop());
            audioSourcesRef.current.clear();
            nextAudioStartTimeRef.current = 0;

            if (outputAudioContextRef.current && outputAudioContextRef.current.state !== 'closed') {
                outputAudioContextRef.current.close().catch(console.error);
            }
            outputAudioContextRef.current = null;
        };
    }, [voiceTrigger, resultData]);

    // Effect to process transcript AFTER a voice session has ended
    useEffect(() => {
        if (prevVoiceStatus === 'active' && voiceSessionStatus === 'inactive') {
            const finalTranscript = transcriptionRef.current;
            if (finalTranscript.userInput.trim() || finalTranscript.modelOutput.trim()) {
                const formattedTranscript = `### Voice Discussion Summary\n\n**You:**\n> ${finalTranscript.userInput.trim()}\n\n**Milimo AI:**\n> ${finalTranscript.modelOutput.trim()}`;
                
                dispatch({ type: 'ADD_TRANSCRIPT_TO_HISTORY', payload: formattedTranscript });
                
                (async () => {
                    if (resultData) {
                        try {
                            const suggestions = await runHypothesisOnTranscript(resultData, formattedTranscript, updateAgentStatus);
                             const aiSuggestionMessage: Message = {
                                id: `suggestion-${Date.now()}`,
                                sender: 'ai',
                                text: "Based on our discussion, here are some new suggestions for our next steps:",
                                data: {
                                    proactiveSuggestions: suggestions,
                                    summary: '', molecules: [], literature: [], experimentalPlan: [], retrosynthesisPlan: [],
                                    knowledgeGraphUpdate: { nodes: [], edges: [] },
                                }
                            };
                            dispatch({ type: 'CHAT_COMPLETE', payload: aiSuggestionMessage });
                        } catch (error) {
                             console.error("Error generating suggestions from transcript:", error);
                        }
                    }
                })();
            }
        }
    }, [voiceSessionStatus, prevVoiceStatus, resultData, updateAgentStatus]);

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop();
            setIsListening(false);
        } else {
            recognitionRef.current?.start();
            setIsListening(true);
        }
    };
    
     const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = (event) => {
                const content = event.target?.result as string;
                dispatch({ type: 'SET_UPLOADED_FILE', payload: { name: file.name, content } });
            };
            reader.readAsText(file);
        }
        if(e.target) e.target.value = '';
    };

    const handlePromptSubmit = async (promptText: string) => {
        if (voiceSessionStatus !== 'inactive') {
            sessionRef.current?.close(); // Ensure session is closed before starting text workflow
        }
        
        const hasInput = promptText.trim() || uploadedFile;
        if (!hasInput || isLoading) return;

        let combinedPrompt = promptText;
        if (uploadedFile) {
            combinedPrompt += `\n\n--- Attached File: ${uploadedFile.name} ---\n${uploadedFile.content}`;
        }
        
        const userMessage: Message = {
            id: Date.now().toString(),
            sender: 'user',
            text: promptText,
            attachment: uploadedFile ? { name: uploadedFile.name } : undefined,
        };
        
        setInputValue('');
        dispatch({ type: 'SET_UPLOADED_FILE', payload: null });
        
        try {
            const { intent } = await determineIntent(combinedPrompt, !!resultData);

            switch (intent) {
                case Intent.DRUG_DISCOVERY_WORKFLOW: {
                    dispatch({ type: 'START_WORKFLOW', payload: { userMessage, currentInput: combinedPrompt } });
                    const results = await runFullWorkflow(
                        combinedPrompt,
                        updateAgentStatus
                    );
                    
                    const aiMessage: Message = {
                        id: (Date.now() + 1).toString(),
                        sender: 'ai',
                        text: "Workflow complete. All results are now available. Explore the detailed findings in the tabs on your right.",
                        data: results,
                    };

                    dispatch({ 
                        type: 'WORKFLOW_COMPLETE', 
                        payload: {
                            results,
                            aiMessage,
                        }
                    });
                    break;
                }
                case Intent.REFINEMENT_WORKFLOW: {
                    if (!resultData) {
                        console.warn("Router suggested refinement, but no data exists. Starting a new workflow instead.");
                        dispatch({ type: 'START_WORKFLOW', payload: { userMessage, currentInput: combinedPrompt } });
                        const results = await runFullWorkflow(
                            combinedPrompt,
                            updateAgentStatus
                        );
                        const aiMessage: Message = { id: (Date.now() + 1).toString(), sender: 'ai', text: "As there was no prior data to refine, a new discovery workflow was initiated. All results are now available.", data: results };
                        dispatch({ type: 'WORKFLOW_COMPLETE', payload: { results, aiMessage }});
                        return;
                    }
                    
                    dispatch({ type: 'START_REFINEMENT', payload: { userMessage, currentInput: combinedPrompt } });
                    const results = await runRefinementWorkflow(
                        combinedPrompt,
                        resultData,
                        updateAgentStatus
                    );

                    const aiMessage: Message = {
                        id: (Date.now() + 1).toString(),
                        sender: 'ai',
                        text: results.summary,
                        data: results,
                    };
                    
                    dispatch({ 
                        type: 'WORKFLOW_COMPLETE', 
                        payload: {
                            results,
                            aiMessage,
                        }
                    });
                    break;
                }
                case Intent.GENERAL_CHAT: {
                    dispatch({ type: 'START_CHAT', payload: userMessage });
                    const chatResponse = await runChat(combinedPrompt, messages);
                    const aiChatMessage: Message = {
                        id: (Date.now() + 1).toString(),
                        sender: 'ai',
                        text: chatResponse.text,
                        data: {
                            proactiveSuggestions: chatResponse.suggestions,
                            // Add dummy fields to satisfy ResultData type
                            summary: '',
                            molecules: [],
                            literature: [],
                            experimentalPlan: [],
                            retrosynthesisPlan: [],
                            knowledgeGraphUpdate: { nodes: [], edges: [] },
                        }
                    };
                    dispatch({ type: 'CHAT_COMPLETE', payload: aiChatMessage });
                    break;
                }
                default:
                    throw new Error(`Unhandled intent: ${intent}`);
            }

        } catch (error) {
            console.error("Workflow failed:", error);
            const errorMessage: Message = {
                id: (Date.now() + 1).toString(),
                sender: 'system',
                text: 'An error occurred during the workflow. Please check the console for details and try again.',
            };
            dispatch({ type: 'WORKFLOW_ERROR', payload: errorMessage });
        }
    };
    
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        handlePromptSubmit(inputValue);
    };

    const handleSuggestionClick = (suggestion: string) => {
        if (isLoading) return;
        handlePromptSubmit(suggestion);
    };
    
    const handleVoiceButtonClick = () => {
        if (voiceSessionStatus === 'inactive' || voiceSessionStatus === 'error') {
            dispatch({ type: 'START_VOICE_SESSION' });
            setVoiceTrigger(Date.now()); // Trigger the effect to start a new session
        } else {
            // Directly close the session via its ref. The `onclose` callback
            // registered in the useEffect will handle dispatching the state update.
            sessionRef.current?.close();
        }
    };

    // Load history from localStorage on mount
    useEffect(() => {
        try {
            const savedHistory = localStorage.getItem('mqdd_history');
            if (savedHistory) {
                dispatch({ type: 'LOAD_HISTORY', payload: JSON.parse(savedHistory) });
            }
        } catch (error) {
            console.error("Failed to load history from localStorage", error);
        }
    }, []);


    // Effect to save session after a workflow completes
    useEffect(() => {
        // Trigger save only when isLoading transitions from true to false and there's resultData
        if (!isLoading && resultData && messages.some(m => m.sender === 'user')) {
             dispatch({
                type: 'SAVE_SESSION',
                payload: {
                    results: resultData,
                    finalMessages: messages,
                    finalAgents: agents,
                },
            });
        }
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isLoading]);
    
    const handleNewSession = () => dispatch({ type: 'NEW_SESSION' });
    const handleSelectHistory = (session: Session) => dispatch({ type: 'SELECT_HISTORY_SESSION', payload: session });

    const getAgentIcon = (agentName: AgentName) => {
        const iconClass = "w-4 h-4 text-neutral-200";
        switch (agentName) {
            case AgentName.TARGET_IDENTIFICATION: return <CrosshairIcon className={iconClass} />;
            case AgentName.LITERATURE: return <BookOpenIcon className={iconClass} />;
            case AgentName.MOLECULAR_DESIGN: return <AtomIcon className={iconClass} />;
            case AgentName.PROPERTY_PREDICTION: return <BeakerIcon className={iconClass} />;
            case AgentName.QUANTUM_SIMULATION: return <ZapIcon className={iconClass} />;
            case AgentName.SYNTHESIZABILITY: return <ClipboardListIcon className={iconClass} />;
            case AgentName.INTERACTION_ANALYSIS: return <NetworkIcon className={iconClass} />;
            case AgentName.RETROSYNTHESIS: return <FlaskConicalIcon className={iconClass} />;
            case AgentName.EXPERIMENTAL_PLANNER: return <ListChecksIcon className={iconClass} />;
            case AgentName.KNOWLEDGE_GRAPH: return <Share2Icon className={iconClass} />;
            case AgentName.FAILURE_ANALYSIS: return <AlertTriangleIcon className={iconClass} />;
            case AgentName.HYPOTHESIS: return <LightbulbIcon className={iconClass} />;
            default: return null;
        }
    };
    
    // Add a key to the status icon to re-trigger animations
    const getStatusIcon = (status: AgentStatus, name: AgentName) => {
        switch (status) {
          case AgentStatus.IDLE: return null;
          case AgentStatus.WORKING: return <LoaderIcon key={`${name}-working`} className="w-4 h-4 text-blue-400 animate-spin" />;
          case AgentStatus.DONE: return <CheckCircleIcon key={`${name}-done`} className="w-4 h-4 text-green-400 animate-pulse-once" />;
          case AgentStatus.ERROR: return <XCircleIcon key={`${name}-error`} className="w-4 h-4 text-red-400" />;
        }
    };
    
    const downloadFile = (content: string, filename: string, mimeType: string) => {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    const handleExportMarkdown = () => {
        if (!resultData) return;
        const { summary, molecules, retrosynthesisPlan, experimentalPlan } = resultData;
        const lead = molecules[0];
        let report = `# Drug Discovery Report: ${lead.name}\n\n`;
        report += `## Executive Summary\n${summary}\n\n`;
        report += `## Lead Candidate: ${lead.name}\n`;
        report += `- **SMILES:** \`${lead.smiles}\`\n`;
        report += `- **Binding Energy:** ${lead.bindingEnergy?.toFixed(2)} kJ/mol\n`;
        report += `- **Synthetic Accessibility Score:** ${lead.saScore?.toFixed(2)} (1=easy, 10=hard)\n\n`;
        if (lead.painsAlerts && lead.painsAlerts.length > 0) {
            report += `**PAINS Alerts:** ${lead.painsAlerts.join(', ')}\n\n`;
        }
        report += `### ADMET Properties\n`;
        Object.entries(lead.admet || {}).forEach(([key, prop]) => {
            const admetProp = prop as AdmetProperty;
            report += `- **${key.charAt(0).toUpperCase() + key.slice(1)}:** ${admetProp.value} (Score: ${admetProp.score?.toFixed(2)})\n`;
        });
        report += `\n## All Candidates\n`;
        report += `| Name | SMILES | Binding Energy (kJ/mol) | Toxicity Score | SA Score |\n`;
        report += `|------|--------|-------------------------|----------------|----------|\n`;
        molecules.forEach(m => {
            report += `| ${m.name} | \`${m.smiles}\` | ${m.bindingEnergy?.toFixed(2)} | ${m.admet?.toxicity.score?.toFixed(2)} | ${m.saScore?.toFixed(2)} |\n`;
        });
        report += `\n## Retrosynthesis Plan\n`;
        retrosynthesisPlan.forEach((step, i) => { report += `${i + 1}. ${step}\n`; });
        report += `\n## Experimental Plan\n`;
        experimentalPlan.forEach((step, i) => { report += `${i + 1}. ${step}\n`; });
        downloadFile(report, `MQDD_Report_${lead.name}.md`, 'text/markdown');
    };

    const handleExportCsv = () => {
        if (!resultData) return;
        const { molecules } = resultData;
        const headers = ['name', 'smiles', 'bindingEnergy', 'saScore', 'painsAlerts', 'logP_value', 'logP_score', 'logS_value', 'logS_score', 'permeability_value', 'permeability_score', 'herg_value', 'herg_score', 'toxicity_value', 'toxicity_score', 'toxicity_evidence'];
        const rows = molecules.map(m => [
            m.name,
            m.smiles,
            m.bindingEnergy?.toFixed(3) || '',
            m.saScore?.toFixed(3) || '',
            `"${m.painsAlerts?.join('; ') || ''}"`,
            m.admet?.logP.value || '',
            m.admet?.logP.score?.toFixed(3) || '',
            m.admet?.logS.value || '',
            m.admet?.logS.score?.toFixed(3) || '',
            m.admet?.permeability.value || '',
            m.admet?.permeability.score?.toFixed(3) || '',
            m.admet?.herg.value || '',
            m.admet?.herg.score?.toFixed(3) || '',
            m.admet?.toxicity.value || '',
            m.admet?.toxicity.score?.toFixed(3) || '',
            `"${m.admet?.toxicity.evidence?.replace(/"/g, '""') || ''}"`
        ].join(','));
        const csvContent = [headers.join(','), ...rows].join('\n');
        downloadFile(csvContent, 'MQDD_Candidates.csv', 'text/csv');
    };

    const handleExportSdf = async () => {
        const smiles = resultData?.molecules[0]?.smiles;
        if (!smiles) return;
        try {
            const cidResponse = await fetch(`https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/smiles/cids/JSON`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: `smiles=${encodeURIComponent(smiles)}`
            });
            const cidData = await cidResponse.json();
            const cid = cidData?.IdentifierList?.CID?.[0];
            if (cid) {
                const sdfUrl = `https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/${cid}/SDF?record_type=3d&response_type=save&response_basename=${resultData?.molecules[0].name || 'candidate'}`;
                window.open(sdfUrl, '_blank');
            } else {
                alert("Could not find molecule in PubChem to generate SDF.");
            }
        } catch (error) {
            console.error("SDF export failed", error);
            alert("An error occurred while trying to export the SDF file.");
        }
    };
    
    const handleTabClick = (tab: ResultTab) => {
        dispatch({ type: 'SET_ACTIVE_TAB', payload: tab });
        setActiveTabKey(Date.now()); // Reset animation key
    }

    const TabButton: React.FC<{tab: ResultTab, label: string}> = ({tab, label}) => (
        <button 
            onClick={() => handleTabClick(tab)} 
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${activeTab === tab ? 'bg-blue-600 text-white' : 'text-neutral-400 hover:bg-neutral-800 hover:text-neutral-200'}`}
        >
            {label}
        </button>
    );

    const TypingIndicator: React.FC = () => (
        <div className="flex items-start gap-4 max-w-4xl mx-auto animate-slideIn">
            <div className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 border bg-neutral-800 border-neutral-700">
                <MilimoLogoIcon className="w-5 h-5" />
            </div>
            <div className="p-4 rounded-lg bg-neutral-900 flex items-center justify-center space-x-1.5">
                <div className="w-2 h-2 bg-neutral-500 rounded-full dot-bounce dot-1"></div>
                <div className="w-2 h-2 bg-neutral-500 rounded-full dot-bounce dot-2"></div>
                <div className="w-2 h-2 bg-neutral-500 rounded-full dot-bounce dot-3"></div>
            </div>
        </div>
    );
    
    const displayedCandidate = selectedMolecule;
    const toxicophoreSmarts = displayedCandidate?.admet?.toxicity.evidence?.startsWith('[') || displayedCandidate?.admet?.toxicity.evidence?.startsWith('c') ? displayedCandidate.admet.toxicity.evidence : undefined;
    const hasPainsAlerts = displayedCandidate && displayedCandidate.painsAlerts && displayedCandidate.painsAlerts.length > 0;

    if (view === 'test') {
        return <Test3DPage onBack={() => setView('main')} />;
    }

    return (
    <div className="flex h-screen bg-neutral-950 text-neutral-200 font-sans antialiased">
        <style>{`
            @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
            .animate-fadeIn { animation: fadeIn 0.4s ease-in-out; }
            
            @keyframes slideIn { 
              from { opacity: 0; transform: translateY(10px); } 
              to { opacity: 1; transform: translateY(0); } 
            }
            .animate-slideIn { animation: slideIn 0.5s ease-out forwards; }
            
            @keyframes pulse-once {
              0% { transform: scale(1); }
              50% { transform: scale(1.2); }
              100% { transform: scale(1); }
            }
            .animate-pulse-once { animation: pulse-once 0.5s ease-in-out; }

            @keyframes bounce-dot {
              0%, 80%, 100% { transform: scale(0); }
              40% { transform: scale(1.0); }
            }
            .dot-bounce {
                animation: bounce-dot 1.4s infinite ease-in-out both;
            }
            .dot-bounce.dot-1 { animation-delay: -0.32s; }
            .dot-bounce.dot-2 { animation-delay: -0.16s; }
        `}</style>
        {/* Left Panel: Control & Agents */}
        <aside className="w-72 bg-neutral-900 flex flex-col p-4 border-r border-neutral-800">
            <div className="flex items-center gap-3 mb-6">
                <MilimoLogoIcon className="w-10 h-10" />
                <div>
                    <h1 className="text-lg font-bold text-neutral-50">Milimo QDD</h1>
                    <p className="text-xs text-neutral-400">AI Co-Scientist Workspace</p>
                </div>
            </div>

            <div className="flex-shrink-0 mb-4">
                <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">Agent Workflow</h2>
                <div className="relative pl-4 py-2 max-h-64 overflow-y-auto pr-2">
                    <div className="absolute left-6 top-5 bottom-5 w-0.5 bg-neutral-800 rounded" />
                    <div className="space-y-4">
                        {agents.map(agent => {
                            const isWorking = agent.status === AgentStatus.WORKING;
                            const isDone = agent.status === AgentStatus.DONE;
                            const isError = agent.status === AgentStatus.ERROR;
                            const isIdle = agent.status === AgentStatus.IDLE && !isLoading;
                            const isQueued = agent.status === AgentStatus.IDLE && isLoading && agent.message === 'Queued';

                            let dotBgClass = 'bg-neutral-700'; // idle
                            if (isQueued) dotBgClass = 'bg-neutral-600';
                            if (isWorking) dotBgClass = 'bg-blue-500';
                            else if (isDone) dotBgClass = 'bg-green-500';
                            else if (isError) dotBgClass = 'bg-red-500';
                            
                            return (
                                <div key={agent.name} className={`relative flex items-start transition-opacity duration-300 ${isIdle ? 'opacity-40' : 'opacity-100'}`}>
                                    <div className="absolute left-0 top-1 w-5 h-5 rounded-full flex items-center justify-center ring-4 ring-neutral-900 z-10">
                                        {isWorking && <div className="absolute w-full h-full bg-blue-500 rounded-full animate-ping" />}
                                        <div className={`relative w-full h-full rounded-full flex items-center justify-center ${dotBgClass}`}>
                                            {getAgentIcon(agent.name)}
                                        </div>
                                    </div>
                                    <div className="ml-8 flex-1">
                                        <div className="flex justify-between items-center">
                                            <span className="text-sm font-medium text-neutral-300">{agent.name}</span>
                                            {getStatusIcon(agent.status, agent.name)}
                                        </div>
                                        <p className="text-xs text-neutral-400 mt-0.5 truncate" title={agent.message}>
                                            {agent.message}
                                        </p>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>

            <div className="flex-1 flex flex-col min-h-0">
                 <div className="flex justify-between items-center mb-3">
                    <h2 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider">Research History</h2>
                    <button onClick={handleNewSession} className="p-1 text-neutral-400 hover:text-white hover:bg-neutral-700 rounded-full" aria-label="New Session">
                        <PlusCircleIcon className="w-5 h-5" />
                    </button>
                </div>
                <div className="flex-1 overflow-y-auto space-y-2 pr-1">
                    {history.length > 0 ? (
                        history.map(session => (
                            <button
                                key={session.id}
                                onClick={() => handleSelectHistory(session)}
                                className={`w-full text-left p-2 rounded-lg transition-colors ${activeSessionId === session.id ? 'bg-blue-600/30' : 'hover:bg-neutral-800'}`}
                            >
                                <p className={`text-sm font-medium truncate ${activeSessionId === session.id ? 'text-blue-300' : 'text-neutral-300'}`}>{session.name}</p>
                                <p className="text-xs text-neutral-500">{new Date(session.timestamp).toLocaleString()}</p>
                            </button>
                        ))
                    ) : (
                        <div className="h-full bg-neutral-800/50 rounded-lg flex flex-col items-center justify-center text-center p-4">
                            <HistoryIcon className="w-6 h-6 text-neutral-500 mb-2" />
                            <p className="text-xs text-neutral-500">Past sessions will appear here.</p>
                        </div>
                    )}
                </div>
            </div>
            
            <div className="flex-shrink-0 mt-4 pt-4 border-t border-neutral-800">
                <button onClick={() => setView('test')} className="flex items-center gap-2 text-sm text-neutral-400 hover:text-neutral-200 transition-colors w-full text-left">
                    <FlaskConicalIcon className="w-4 h-4" />
                    <span>3D Viewer Test Page</span>
                </button>
            </div>
        </aside>

        {/* Center Panel: Interaction Canvas */}
        <main className="flex-1 flex flex-col bg-neutral-950 min-w-0">
             <div ref={mainContentRef} className="flex-1 overflow-y-auto p-6 space-y-6">
                {messages.map((msg) => {
                    if (msg.sender === 'system') {
                       const isTranscript = msg.text.startsWith('### Voice Discussion Summary');
                       return (
                            <div key={msg.id} className={`flex justify-center items-center my-4 animate-slideIn ${isTranscript ? 'w-full max-w-4xl mx-auto' : ''}`}>
                                {isTranscript ? (
                                     <div className="w-full p-4 rounded-lg bg-neutral-900 border border-neutral-800 prose prose-sm prose-invert max-w-none">
                                        <ReactMarkdown>{msg.text}</ReactMarkdown>
                                     </div>
                                ) : (
                                    <div className="flex items-center gap-2 text-xs text-neutral-400 bg-neutral-900 px-3 py-1 rounded-full border border-neutral-800">
                                        <LoaderIcon className="w-3 h-3 animate-spin" />
                                        <span>{msg.text}</span>
                                    </div>
                                )}
                            </div>
                        );
                    }
                    return (
                        <div key={msg.id} className={`flex flex-col gap-2 max-w-4xl mx-auto animate-slideIn ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                            <div className={`flex items-start gap-4 w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
                                {msg.sender !== 'user' && (
                                    <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 border ${msg.sender === 'ai' ? 'bg-neutral-800 border-neutral-700' : 'bg-transparent border-transparent'}`}>
                                        {msg.sender === 'ai' ? <MilimoLogoIcon className="w-5 h-5" /> : null}
                                    </div>
                                )}
                                <div className={`p-4 rounded-lg prose prose-sm prose-invert max-w-none ${msg.sender === 'user' ? 'bg-blue-600 text-white' : 'bg-neutral-900'}`}>
                                   <h3 className="font-semibold mb-1 not-prose">{msg.sender === 'ai' ? 'Milimo AI' : 'User'}</h3>
                                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                                    {msg.sender === 'user' && msg.attachment && (
                                        <div className="mt-3 pt-2 border-t border-blue-500">
                                            <div className="flex items-center gap-2 text-xs text-blue-100 bg-black/20 px-2 py-1 rounded-md">
                                                <FileIcon className="w-3.5 h-3.5" />
                                                <span>{msg.attachment.name}</span>
                                            </div>
                                        </div>
                                    )}
                                </div>
                                 {msg.sender === 'user' && (
                                    <div className="w-8 h-8 rounded-full bg-neutral-700 flex items-center justify-center flex-shrink-0">
                                        <UserIcon className="w-5 h-5 text-neutral-300"/>
                                    </div>
                                )}
                            </div>
                            {msg.sender === 'ai' && msg.data?.proactiveSuggestions && msg.data.proactiveSuggestions.length > 0 && (
                                <div className="flex flex-wrap gap-2 pl-12">
                                    {msg.data.proactiveSuggestions.map((suggestion, i) => (
                                        <button
                                            key={i}
                                            onClick={() => handleSuggestionClick(suggestion)}
                                            className="px-3 py-1.5 bg-neutral-800/80 rounded-lg text-sm text-blue-400 hover:bg-neutral-700/80 transition-colors"
                                        >
                                            {suggestion}
                                        </button>
                                    ))}
                                </div>
                            )}
                        </div>
                    );
                })}
                {isLoading && <TypingIndicator />}
            </div>
            
            <div className="p-4 border-t border-neutral-800">
                {uploadedFile && (
                    <div className="max-w-4xl mx-auto mb-2">
                        <div className="flex items-center justify-between text-sm bg-neutral-800 px-3 py-2 rounded-md animate-fadeIn">
                            <div className="flex items-center gap-2 text-neutral-300">
                                <FileIcon className="w-4 h-4" />
                                <span className="font-mono">{uploadedFile.name}</span>
                            </div>
                            <button onClick={() => dispatch({ type: 'SET_UPLOADED_FILE', payload: null })} className="text-neutral-500 hover:text-neutral-200">
                                <XCircleIcon className="w-4 h-4" />
                            </button>
                        </div>
                    </div>
                )}
                 <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex items-center gap-2 p-1 bg-neutral-900 rounded-lg border border-neutral-700 focus-within:border-blue-500 transition-colors">
                    <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".pdb,.sdf,.mol" className="hidden" />
                    <button type="button" onClick={() => fileInputRef.current?.click()} className="p-2 text-neutral-400 hover:bg-neutral-700 rounded-md" disabled={isLoading} aria-label="Attach file">
                        <FileIcon className="w-5 h-5" />
                    </button>
                    <input
                        type="text"
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        placeholder={resultData ? "Suggest a refinement..." : "Describe your research goal..."}
                        className="flex-1 bg-transparent focus:outline-none px-3 py-2"
                        disabled={isLoading}
                        onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) handleSubmit(e); }}
                        aria-label="Chat input"
                    />
                    <button type="button" onClick={toggleListening} className={`p-2 rounded-md ${isListening ? 'bg-red-500 text-white' : 'text-neutral-400 hover:bg-neutral-700'}`} disabled={isLoading} aria-label={isListening ? 'Stop listening' : 'Start listening'}>
                        <MicIcon className="w-5 h-5" />
                    </button>
                    <button type="submit" className="p-2 bg-neutral-700 rounded-md hover:bg-neutral-600 disabled:bg-neutral-800 disabled:cursor-not-allowed" disabled={isLoading || (!inputValue.trim() && !uploadedFile)} aria-label="Send message">
                        <SendIcon className="w-5 h-5" />
                    </button>
                </form>
            </div>
        </main>

        {/* Right Panel: Results Explorer */}
        <aside className="w-[420px] bg-neutral-900 border-l border-neutral-800 flex flex-col min-h-0">
            <div className="p-4 border-b border-neutral-800 flex justify-between items-center flex-shrink-0">
                <h2 className="text-base font-semibold text-neutral-100">Results Explorer</h2>
                <div className="flex items-center gap-2">
                     <button
                        onClick={handleVoiceButtonClick}
                        disabled={!resultData || voiceSessionStatus === 'connecting'}
                        className={`flex items-center gap-1.5 px-3 py-1 border rounded-md text-sm font-medium transition-all duration-300 ${
                            voiceSessionStatus === 'active'
                                ? 'bg-red-600 border-red-500 text-white animate-pulse'
                                : 'bg-neutral-800 border-neutral-700 text-neutral-300 hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed'
                        }`}
                        aria-label={voiceSessionStatus === 'active' ? 'End voice session' : 'Start voice session'}
                    >
                        {voiceSessionStatus === 'inactive' && <MicIcon className="w-4 h-4" />}
                        {voiceSessionStatus === 'connecting' && <LoaderIcon className="w-4 h-4 animate-spin" />}
                        {voiceSessionStatus === 'active' && <StopCircleIcon className="w-4 h-4" />}
                        <span>
                            {voiceSessionStatus === 'inactive' && 'Discuss'}
                            {voiceSessionStatus === 'connecting' && '...'}
                            {voiceSessionStatus === 'active' && 'End Call'}
                        </span>
                    </button>
                    <div className="relative">
                        <button
                            onClick={() => setIsExportMenuOpen(prev => !prev)}
                            disabled={!resultData}
                            className="flex items-center gap-1 px-3 py-1 bg-neutral-800 border border-neutral-700 rounded-md text-sm text-neutral-300 hover:bg-neutral-700 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <DownloadIcon className="w-4 h-4" />
                            Export
                        </button>
                        {isExportMenuOpen && (
                            <div onMouseLeave={() => setIsExportMenuOpen(false)} className="absolute right-0 mt-2 w-48 bg-neutral-800 border border-neutral-700 rounded-md shadow-lg z-20">
                                <button onClick={() => { handleExportMarkdown(); setIsExportMenuOpen(false); }} className="block w-full text-left px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-700">Summary (.md)</button>
                                <button onClick={() => { handleExportCsv(); setIsExportMenuOpen(false); }} className="block w-full text-left px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-700">Candidates (.csv)</button>
                                <button onClick={() => { handleExportSdf(); setIsExportMenuOpen(false); }} className="block w-full text-left px-4 py-2 text-sm text-neutral-300 hover:bg-neutral-700">Lead (.sdf)</button>
                            </div>
                        )}
                    </div>
                </div>
            </div>
            
            {resultData ? (
                <>
                    <div className="p-2 border-b border-neutral-800 flex-shrink-0">
                        <div className="flex items-center gap-1 flex-wrap">
                           <TabButton tab="summary" label="Summary" />
                           <TabButton tab="candidate" label="Lead" />
                           <TabButton tab="analysis" label="Analysis" />
                           <TabButton tab="synthesis" label="Synthesis" />
                           <TabButton tab="knowledge" label="Knowledge" />
                           <TabButton tab="plan" label="Plan" />
                           <TabButton tab="literature" label="Literature" />
                        </div>
                    </div>
                    <div key={activeTabKey} className="flex-1 overflow-y-auto p-4 space-y-6 animate-fadeIn min-h-0">
                       {activeTab === 'summary' && (
                            <div>
                                {resultData.failureAnalysisReport && (
                                    <div className="mb-6">
                                        <h3 className="text-sm font-semibold text-amber-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                                            <AlertTriangleIcon className="w-4 h-4" />
                                            Failure Analysis Report
                                        </h3>
                                        <div className="prose prose-sm prose-invert max-w-none bg-amber-900/50 border border-amber-800 p-3 rounded-lg text-amber-200">
                                            <ReactMarkdown>{resultData.failureAnalysisReport}</ReactMarkdown>
                                        </div>
                                    </div>
                                )}
                                <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">Executive Summary</h3>
                                <div className="prose prose-sm prose-invert max-w-none bg-neutral-800/50 p-3 rounded-lg">
                                    <ReactMarkdown>{resultData.summary}</ReactMarkdown>
                                </div>
                                {resultData.proactiveSuggestions && resultData.proactiveSuggestions.length > 0 && (
                                    <div className="mt-6">
                                        <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">Suggested Next Steps</h3>
                                        <div className="space-y-2">
                                            {resultData.proactiveSuggestions.map((suggestion, i) => (
                                                <button
                                                    key={i}
                                                    onClick={() => handleSuggestionClick(suggestion)}
                                                    className="w-full text-left p-3 bg-neutral-800/50 rounded-lg text-sm text-blue-400 hover:bg-neutral-700/50 transition-colors"
                                                >
                                                    {suggestion}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        {activeTab === 'candidate' && displayedCandidate && (
                            <>
                                <div>
                                    <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">Selected Candidate</h3>
                                    <div className="bg-neutral-800/50 p-3 rounded-lg">
                                        <div className="flex items-start justify-between">
                                            <h4 className="font-bold text-base text-neutral-100 flex-1">{displayedCandidate.name}</h4>
                                            {hasPainsAlerts && (
                                                <div className="relative group flex-shrink-0 ml-2">
                                                    <AlertTriangleIcon className="w-5 h-5 text-amber-400" />
                                                    <div className="absolute bottom-full mb-2 right-0 w-48 bg-neutral-900 text-xs text-neutral-200 p-2 rounded-md border border-neutral-700 shadow-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none">
                                                        <h5 className="font-bold mb-1">PAINS Alert</h5>
                                                        <p>This molecule contains promiscuous substructures:</p>
                                                        <ul className="list-disc list-inside">
                                                            {displayedCandidate.painsAlerts?.map(p => <li key={p}>{p}</li>)}
                                                        </ul>
                                                    </div>
                                                </div>
                                            )}
                                        </div>

                                        <p className="text-xs text-blue-400 font-mono break-all mb-2">{displayedCandidate.smiles}</p>
                                        <div className="flex justify-between text-sm text-neutral-300 mb-3">
                                            <p>Binding Energy: <span className="font-semibold text-green-400">{displayedCandidate.bindingEnergy?.toFixed(2)} kJ/mol</span></p>
                                            <p>SA Score: <span className="font-semibold text-purple-400">{displayedCandidate.saScore?.toFixed(2)}</span></p>
                                        </div>
                                         <MoleculeViewer3D smiles={displayedCandidate.smiles} pdbId={resultData.pdbId} interactions={displayedCandidate.interactions}/>
                                    </div>
                                </div>
                                <div>
                                    <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">ADMET Properties</h3>
                                    <div className="text-xs space-y-2 bg-neutral-800/50 p-3 rounded-lg">
                                        {displayedCandidate.admet ? (
                                             <table className="w-full">
                                                <tbody>
                                                    {Object.entries(displayedCandidate.admet).map(([key, prop]) => {
                                                        const admetProp = prop as AdmetProperty;
                                                        const keyMap: Record<string, string> = { 'logP': 'LogP', 'logS': 'LogS', 'permeability': 'Permeability', 'herg': 'hERG', 'toxicity': 'Toxicity'};
                                                        return (
                                                            <tr key={key}>
                                                                <td className="capitalize text-neutral-400 py-1 pr-2">{keyMap[key] || key}</td> 
                                                                <td className="font-medium text-neutral-200 text-right py-1">{admetProp.value}</td>
                                                            </tr>
                                                        );
                                                    })}
                                                </tbody>
                                             </table>
                                        ) : <p>No ADMET data available.</p>}
                                    </div>
                                    {toxicophoreSmarts && (
                                        <div className="mt-2 bg-neutral-800/50 p-3 rounded-lg">
                                             <p className="text-xs text-neutral-400 mb-1">Potential Toxicophore Highlighted:</p>
                                            <MoleculeViewer smiles={displayedCandidate.smiles} highlightSmarts={toxicophoreSmarts} className="w-full h-auto rounded-md bg-neutral-800" />
                                        </div>
                                    )}
                                </div>
                            </>
                        )}
                        {activeTab === 'analysis' && (
                            <div>
                                <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">Candidate Analysis</h3>
                                <div className="bg-neutral-800/50 p-3 rounded-lg">
                                    <CandidateComparisonChart 
                                        molecules={resultData.molecules} 
                                        onMoleculeClick={(mol) => dispatch({ type: 'SET_SELECTED_MOLECULE', payload: mol })}
                                        selectedMolecule={selectedMolecule}
                                    />
                                </div>
                                <div className="mt-4 bg-neutral-800/50 p-3 rounded-lg">
                                    <table className="w-full text-xs text-left">
                                        <thead>
                                            <tr className="border-b border-neutral-700">
                                                <th className="p-2">Name</th>
                                                <th className="p-2 text-right">Binding (kJ/mol)</th>
                                                <th className="p-2 text-right">Toxicity</th>
                                                <th className="p-2 text-right">SA Score</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {resultData.molecules.map((mol, i) => (
                                                <tr 
                                                    key={i} 
                                                    className={`border-b border-neutral-700/50 transition-colors cursor-pointer hover:bg-neutral-700/30 ${mol.smiles === selectedMolecule?.smiles ? 'bg-blue-600/20' : ''}`}
                                                    onClick={() => dispatch({ type: 'SET_SELECTED_MOLECULE', payload: mol })}
                                                >
                                                    <td className="p-2 font-medium">{mol.name}</td>
                                                    <td className="p-2 text-right font-mono">{mol.bindingEnergy?.toFixed(2)}</td>
                                                    <td className="p-2 text-right font-mono">{mol.admet?.toxicity.score?.toFixed(2)}</td>
                                                    <td className="p-2 text-right font-mono">{mol.saScore?.toFixed(2)}</td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        )}
                        {activeTab === 'synthesis' && (
                             <div>
                                <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">Retrosynthesis Plan</h3>
                                 <div className="text-xs text-neutral-500 mb-2 p-2 bg-neutral-800 rounded-md">
                                    Showing synthesis for lead candidate: <span className="font-semibold text-neutral-300">{resultData.molecules[0]?.name}</span>
                                 </div>
                                <div className="bg-neutral-800/50 p-4 rounded-lg">
                                    <ol className="list-decimal list-inside space-y-3 text-sm text-neutral-300">
                                        {resultData.retrosynthesisPlan.map((step, i) => <li key={i}>{step}</li>)}
                                    </ol>
                                </div>
                            </div>
                        )}
                        {activeTab === 'knowledge' && (
                             <div>
                                <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">Knowledge Graph</h3>
                                <div className="bg-neutral-800/50 p-3 rounded-lg">
                                    <KnowledgeGraph data={resultData.knowledgeGraphUpdate} />
                                </div>
                            </div>
                        )}
                         {activeTab === 'plan' && (
                            <div>
                                <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">Experimental Plan</h3>
                                <div className="bg-neutral-800/50 p-4 rounded-lg">
                                    <ol className="list-decimal list-inside space-y-3 text-sm text-neutral-300">
                                        {resultData.experimentalPlan.map((step, i) => <li key={i}>{step}</li>)}
                                    </ol>
                                </div>
                            </div>
                        )}
                         {activeTab === 'literature' && (
                            <div>
                                <h3 className="text-sm font-semibold text-neutral-400 uppercase tracking-wider mb-3">Cited Literature</h3>
                                <div className="space-y-3">
                                    {resultData.literature.map((ref, i) => (
                                        <div key={i} className="bg-neutral-800/50 p-3 rounded-lg text-xs">
                                            <a href={ref.url} target="_blank" rel="noopener noreferrer" className="font-semibold text-blue-400 hover:underline">{ref.title}</a>
                                            <p className="text-neutral-400 mt-1">{ref.summary}</p>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </>
            ) : (
                <div className="h-full flex flex-col items-center justify-center text-center p-4">
                    <NetworkIcon className="w-10 h-10 text-neutral-600 mb-3" />
                    <h3 className="font-semibold text-neutral-300">Awaiting Results</h3>
                    <p className="text-sm text-neutral-500">Run a workflow to see results here.</p>
                </div>
            )}
        </aside>
    </div>
    );
};

export default App;