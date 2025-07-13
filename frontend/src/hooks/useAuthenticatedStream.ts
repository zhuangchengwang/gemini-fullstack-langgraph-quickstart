import { useStream } from "@langchain/langgraph-sdk/react";
import { Client } from "@langchain/langgraph-sdk";
import { useAuth } from "@/contexts/AuthContext";
import { useEffect, useMemo } from "react";

export function useAuthenticatedStream<T extends Record<string, unknown>>(options: any) {
  const { token, isAuthenticated, setShowLoginModal } = useAuth();
  
  // 创建带认证的 LangGraph Client，确保所有请求都包含认证头
  const client = useMemo(() => {
    if (!token) return null;
    
    return new Client({
      apiUrl: options.apiUrl,
      defaultHeaders: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        // 添加自定义请求头，这些会被传递到LangGraph认证函数
        'X-Client-Version': '1.0.0',
        'X-Client-Platform': 'web',
        'X-Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
        'X-Language': navigator.language,
      }
    });
  }, [token, options.apiUrl]);
  
  // 为 LangGraph SDK 正确配置认证，确保所有内部请求都使用认证
  const authenticatedOptions = useMemo(() => {
    // 基础配置，确保所有情况下都有正确的apiUrl
    const baseOptions = {
      ...options,
      apiUrl: options.apiUrl, // 强制使用传入的apiUrl
      assistantId: options.assistantId,
      streamMode: 'values',
    };

    if (!token || !client) {
      return {
        ...baseOptions,
        headers: {
          'Content-Type': 'application/json',
        }
      };
    }

    return {
      ...baseOptions,
      // 强制使用带认证的 client，确保所有 SDK 内部请求都经过这个 client
      client: client,
      // 同时也在 options 级别设置 headers 作为备用
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        // 添加自定义请求头，这些会被传递到LangGraph认证函数
        'X-Client-Version': '1.0.0',
        'X-Client-Platform': 'web',
        'X-Timezone': Intl.DateTimeFormat().resolvedOptions().timeZone,
        'X-Language': navigator.language,
        ...options.headers,
      },
    };
  }, [token, client, options]);
  
  console.log('🔐 认证流配置:', { 
    hasToken: !!token, 
    isAuthenticated,
    apiUrl: options.apiUrl,
    finalApiUrl: authenticatedOptions.apiUrl, // 添加最终使用的URL
    headers: authenticatedOptions.headers,
    assistantId: options.assistantId,
    hasClient: !!client,
    hasCustomClient: !!authenticatedOptions.client, // 添加client状态
  });
  
  // 只有在有认证信息时才创建 stream
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
  const authenticatedSubmit = (data: any, config?: any) => {
    console.log('📤 提交数据，Token状态:', { hasToken: !!token, isAuthenticated });
    
    if (!token || !isAuthenticated) {
      console.log('❌ 没有认证信息，显示登录模态框');
      setShowLoginModal(true);
      return;
    }
    
    // 扩展配置，传递用户特定的参数和URL参数
    const enhancedConfig = {
      ...config,
      configurable: {
        // 用户自定义配置
        user_preference: "chinese", // 用户语言偏好
        search_region: "zh-CN",     // 搜索区域
        personalization_enabled: true,
        
        // 从URL或其他来源获取的参数
        response_format: new URLSearchParams(window.location.search).get('format') || 'standard',
        search_depth: new URLSearchParams(window.location.search).get('depth') || 'standard',
        max_results: new URLSearchParams(window.location.search).get('max_results') || '10',
        include_sources: new URLSearchParams(window.location.search).get('sources') !== 'false',
        
        // 客户端环境信息
        client_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        client_language: navigator.language,
        client_platform: 'web',
        screen_resolution: `${window.screen.width}x${window.screen.height}`,
        
        // LangGraph会自动添加 langgraph_auth_user 字段
        ...config?.configurable,
      },
      
      // 添加请求元数据
      metadata: {
        client_info: {
          user_agent: navigator.userAgent,
          timestamp: new Date().toISOString(),
          session_id: sessionStorage.getItem('session_id') || 'new_session',
          page_url: window.location.href
        },
        request_context: {
          source: 'frontend_submit',
          feature_flags: ['enhanced_search', 'real_time_updates'],
          experiment_id: 'exp_001'
        },
        ...config?.metadata
      }
    };
    
    console.log('✅ 使用认证提交数据, Data:', { 
      messagesCount: data.messages?.length,
      hasToken: !!token,
      config: enhancedConfig,
      urlParams: Object.fromEntries(new URLSearchParams(window.location.search))
    });
    
    originalSubmit(data, enhancedConfig);
  };

  // 添加一个辅助函数来动态更新URL参数
  const submitWithUrlParams = (data: any, urlParams: Record<string, string> = {}) => {
    // 将参数添加到URL
    const url = new URL(window.location.href);
    Object.entries(urlParams).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
    
    // 更新URL（不刷新页面）
    window.history.replaceState({}, '', url.toString());
    
    // 提交数据
    authenticatedSubmit(data);
  };

  return {
    ...stream,
    submit: authenticatedSubmit,
    submitWithUrlParams, // 新增的辅助函数
  };
} 