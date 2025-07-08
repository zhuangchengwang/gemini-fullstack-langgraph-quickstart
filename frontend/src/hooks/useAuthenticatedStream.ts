import { useStream } from "@langchain/langgraph-sdk/react";
import { useAuth } from "@/contexts/AuthContext";
import { useEffect } from "react";

export function useAuthenticatedStream<T extends Record<string, unknown>>(options: any) {
  const { token, isAuthenticated, setShowLoginModal } = useAuth();
  
  // Create authenticated options
  const authenticatedOptions = {
    ...options,
    headers: {
      ...options.headers,
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  };
  
  const stream = useStream<T>(authenticatedOptions);
  
  // Check authentication status and show login modal if needed
  useEffect(() => {
    if (!isAuthenticated && !token) {
      setShowLoginModal(true);
    }
  }, [isAuthenticated, token, setShowLoginModal]);
  
  // Override submit to include auth header
  const originalSubmit = stream.submit;
  const authenticatedSubmit = (data: any) => {
    if (!token) {
      setShowLoginModal(true);
      return;
    }
    originalSubmit(data);
  };
  
  return {
    ...stream,
    submit: authenticatedSubmit,
  };
} 