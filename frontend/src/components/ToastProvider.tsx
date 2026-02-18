"use client";

import {
    createContext,
    useContext,
    useState,
    useCallback,
    type ReactNode,
} from "react";
import { CheckCircle2, AlertCircle, Info, AlertTriangle, X } from "lucide-react";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
    id: string;
    type: ToastType;
    message: string;
}

interface ToastContextValue {
    toast: (type: ToastType, message: string) => void;
}

const ToastContext = createContext<ToastContextValue>({
    toast: () => { },
});

export function useToast() {
    return useContext(ToastContext);
}

const TOAST_ICONS: Record<ToastType, ReactNode> = {
    success: <CheckCircle2 className="w-4 h-4" />,
    error: <AlertCircle className="w-4 h-4" />,
    info: <Info className="w-4 h-4" />,
    warning: <AlertTriangle className="w-4 h-4" />,
};

const TOAST_STYLES: Record<ToastType, string> = {
    success:
        "bg-emerald-500/10 border-emerald-500/30 text-emerald-400",
    error:
        "bg-red-500/10 border-red-500/30 text-red-400",
    info:
        "bg-blue-500/10 border-blue-500/30 text-blue-400",
    warning:
        "bg-amber-500/10 border-amber-500/30 text-amber-400",
};

export default function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const addToast = useCallback((type: ToastType, message: string) => {
        const id = Math.random().toString(36).slice(2);
        setToasts((prev) => [...prev, { id, type, message }]);
        // Auto-dismiss after 4s
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 4000);
    }, []);

    const removeToast = useCallback((id: string) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ toast: addToast }}>
            {children}
            {/* Toast container */}
            <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 max-w-sm">
                {toasts.map((t) => (
                    <div
                        key={t.id}
                        className={`flex items-center gap-3 px-4 py-3 rounded-xl border backdrop-blur-xl shadow-2xl animate-slide-up ${TOAST_STYLES[t.type]}`}
                    >
                        {TOAST_ICONS[t.type]}
                        <span className="text-sm flex-1">{t.message}</span>
                        <button
                            onClick={() => removeToast(t.id)}
                            className="p-0.5 rounded hover:bg-white/10 transition-colors opacity-60 hover:opacity-100"
                        >
                            <X className="w-3.5 h-3.5" />
                        </button>
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}
