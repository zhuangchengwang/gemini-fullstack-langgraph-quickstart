"""
LangGraph 用户上下文传递演示

演示如何在 LangGraph 中传递用户信息和自定义参数到 agent
"""

import asyncio
from langchain_core.messages import HumanMessage
from agent.graph import graph


async def demo_user_context_passing():
    """演示用户上下文传递的完整流程"""
    
    print("🚀 LangGraph 用户上下文传递演示")
    print("=" * 50)
    
    # 模拟不同用户的配置
    user_scenarios = [
        {
            "name": "中文用户张三",
            "state": {
                "messages": [HumanMessage(content="人工智能的发展趋势")],
                "user_id": "user_zh_001",
                "user_metadata": {
                    "username": "张三",
                    "region": "China",
                    "subscription_tier": "premium"
                }
            },
            "config": {
                "configurable": {
                    "user_preference": "chinese",
                    "search_region": "zh-CN",
                    "personalization_enabled": True,
                    "max_results": 10,
                    # 模拟认证用户信息（实际由 LangGraph auth 自动注入）
                    "langgraph_auth_user": {
                        "identity": "user_zh_001",
                        "username": "张三",
                        "email": "zhangsan@example.com",
                        "is_authenticated": True,
                        "roles": ["premium_user"],
                        "permissions": ["search", "advanced_search"]
                    }
                }
            }
        },
        {
            "name": "英文用户John",
            "state": {
                "messages": [HumanMessage(content="Future of artificial intelligence")],
                "user_id": "user_en_001", 
                "user_metadata": {
                    "username": "John",
                    "region": "US",
                    "subscription_tier": "basic"
                }
            },
            "config": {
                "configurable": {
                    "user_preference": "english",
                    "search_region": "en-US", 
                    "personalization_enabled": True,
                    "max_results": 5,
                    # 模拟认证用户信息
                    "langgraph_auth_user": {
                        "identity": "user_en_001",
                        "username": "John",
                        "email": "john@example.com",
                        "is_authenticated": True,
                        "roles": ["basic_user"],
                        "permissions": ["search"]
                    }
                }
            }
        }
    ]
    
    for scenario in user_scenarios:
        print(f"\n🔍 测试场景: {scenario['name']}")
        print("-" * 30)
        
        try:
            # 执行图，传递用户状态和配置
            result = await graph.ainvoke(
                scenario["state"], 
                config=scenario["config"]
            )
            
            print(f"✅ 执行成功")
            print(f"📝 用户ID: {result.get('user_id', 'N/A')}")
            print(f"👤 用户元数据: {result.get('user_metadata', {})}")
            
            # 显示生成的消息
            messages = result.get("messages", [])
            if messages:
                final_message = messages[-1]
                print(f"🤖 AI回答预览: {final_message.content[:100]}...")
            
        except Exception as e:
            print(f"❌ 执行失败: {e}")
        
        print()


def demo_config_examples():
    """展示不同的配置传递方式"""
    
    print("\n📋 配置传递方式示例")
    print("=" * 50)
    
    # 方式1：通过状态传递
    print("方式1: 通过图状态传递用户信息")
    state_example = {
        "messages": [HumanMessage(content="Hello")],
        "user_id": "user123",
        "user_metadata": {
            "preference": "fast_response",
            "tier": "premium"
        }
    }
    print(f"State: {state_example}")
    
    # 方式2：通过 RunnableConfig 传递
    print("\n方式2: 通过 RunnableConfig.configurable 传递")
    config_example = {
        "configurable": {
            # 自定义配置
            "search_depth": "detailed",
            "response_format": "structured",
            "language": "zh-CN",
            
            # LangGraph 自动注入的认证信息
            "langgraph_auth_user": {
                "identity": "user123",
                "permissions": ["read", "write"],
                "metadata": {"subscription": "pro"}
            }
        }
    }
    print(f"Config: {config_example}")
    
    # 方式3：Query参数和POST body组合
    print("\n方式3: API请求参数映射")
    api_mapping = {
        "URL": "/threads/{thread_id}/runs",
        "Headers": {
            "Authorization": "Bearer jwt_token",
            "Content-Type": "application/json"
        },
        "Query Params": {
            "stream": "true",
            "user_preference": "chinese",
            "region": "asia"
        },
        "POST Body": {
            "input": {
                "messages": [...],
                "user_context": {
                    "user_id": "from_jwt",
                    "preferences": "from_query_params"
                }
            },
            "config": {
                "configurable": {
                    "custom_setting": "from_body"
                }
            }
        }
    }
    print(f"API Mapping: {api_mapping}")


async def demo_permission_based_access():
    """演示基于权限的访问控制"""
    
    print("\n🔐 权限控制演示")
    print("=" * 50)
    
    # 不同权限级别的用户
    permission_scenarios = [
        {
            "user": "admin_user",
            "permissions": ["read", "write", "admin", "advanced_search"],
            "should_succeed": True
        },
        {
            "user": "premium_user", 
            "permissions": ["read", "write", "advanced_search"],
            "should_succeed": True
        },
        {
            "user": "basic_user",
            "permissions": ["read"],
            "should_succeed": False  # 假设需要 "advanced_search" 权限
        }
    ]
    
    for scenario in permission_scenarios:
        print(f"\n👤 用户: {scenario['user']}")
        print(f"🔑 权限: {scenario['permissions']}")
        print(f"🎯 预期结果: {'成功' if scenario['should_succeed'] else '权限不足'}")


if __name__ == "__main__":
    print("🎯 LangGraph 用户上下文传递完整演示")
    print("这个演示展示了如何在 LangGraph 中传递和使用用户信息")
    print()
    
    # 显示配置示例
    demo_config_examples()
    
    # 显示权限控制示例  
    asyncio.run(demo_permission_based_access())
    
    # 执行实际的图调用演示（需要真实的环境）
    # asyncio.run(demo_user_context_passing()) 