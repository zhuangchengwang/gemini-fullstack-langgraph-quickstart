import { useStream } from "@langchain/langgraph-sdk/react";
import { useAuth } from "@/contexts/AuthContext";
import { useEffect } from "react";

export function useAuthenticatedStream<T extends Record<string, unknown>>(options: any) {
  const { token, isAuthenticated, setShowLoginModal } = useAuth();
  
  // 为 LangGraph SDK 正确配置认证
  const authenticatedOptions = {
    ...options,
    // 在 options 级别设置默认认证头
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      ...options.headers,
    },
    // 为 SDK 内部请求配置认证
    streamMode: 'values',
    ...(token ? {
      defaultHeaders: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      }
    } : {}),
  };
  
  console.log('🔐 认证流配置:', { 
    hasToken: !!token, 
    isAuthenticated,
    apiUrl: options.apiUrl,
    headers: authenticatedOptions.headers,
    assistantId: options.assistantId
  });
  
  const stream = useStream<T>(authenticatedOptions);
  
  // Check authentication status and show login modal if needed
  useEffect(() => {
    if (!isAuthenticated || !token) {
      console.log('❌ 未认证，显示登录模态框');
      setShowLoginModal(true);
    }
  }, [isAuthenticated, token, setShowLoginModal]);
  
  // Override submit to include auth header and check authentication
  const originalSubmit = stream.submit;
  const authenticatedSubmit = (data: any) => {
    console.log('📤 提交数据，Token状态:', { hasToken: !!token, isAuthenticated });
    
    if (!token || !isAuthenticated) {
      console.log('❌ 没有认证信息，显示登录模态框');
      setShowLoginModal(true);
      return;
    }
    
    console.log('✅ 使用认证提交数据, Data:', { 
      messagesCount: data.messages?.length,
      hasToken: !!token 
    });
    originalSubmit(data);
  };
  
  // Override stop to ensure it doesn't cause authentication issues
  const originalStop = stream.stop;
  const authenticatedStop = () => {
    console.log('⏹️ 停止流，保持认证状态');
    originalStop();
  };
  
  // Monitor stream errors for authentication issues
  useEffect(() => {
    if (stream.error) {
      console.error('🚨 Stream错误:', stream.error);
      
      // Check if error is related to authentication
      const errorString = String(stream.error);
      if (errorString.includes('401') || 
          errorString.includes('Unauthorized') ||
          errorString.includes('Authentication required')) {
        console.log('🔒 检测到认证错误，显示登录模态框');
        setShowLoginModal(true);
      }
    }
  }, [stream.error, setShowLoginModal]);
  
  return {
    ...stream,
    submit: authenticatedSubmit,
    stop: authenticatedStop,
  };
} 